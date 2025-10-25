"""Implementation of the Kedro Expectations Hooks."""

import importlib
import multiprocessing.managers
import multiprocessing.process
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, Optional, cast

import fsspec
import great_expectations as ge
from great_expectations.checkpoint.checkpoint import Checkpoint, CheckpointResult
from great_expectations.core import (
    ExpectationSuiteValidationResult,
    ExpectationValidationResult,
    RunIdentifier,
)
from great_expectations.core.suite_parameters import SuiteParameterDict
from great_expectations.data_context.types.resource_identifiers import (
    ExpectationSuiteIdentifier,
    ValidationResultIdentifier,
)
from kedro.framework.context import KedroContext
from kedro.framework.hooks import hook_impl
from kedro.io import DataCatalog
from kedro.pipeline.node import Node
from kedro_datasets.partitions.partitioned_dataset import PartitionedDataset
from pandas import DataFrame as PandasDataFrame

from .constants import CONSTANT_EMAIL_SETTING_CUMULATE, CONSTANT_EMAIL_SETTING_STORE
from .exceptions import SuiteValidationFailure
from .notification import BaseNotifier
from .utils import (
    base_ge_folder_exists,
    delete_checkpoints,
    dot_to_underscore,
    get_all_expectations,
    get_suite_name,
    load_checkpoints,
    location_is_kedro_root_folder,
    split_suite_name,
    store_checkpoints,
    validate,
)

RUN_NAME = "kedro_expectations_auto_validation"


class KedroExpectationsCheckpointResult:

    def __init__(self, suite_name: str, run_results: dict, success: bool):
        self.suite_name = suite_name
        self.run_results = run_results
        self.success = success


class KedroExpectationsHooks:
    """Implementation of the Kedro Expectations Hooks."""

    def __init__(
        self,
        on_failure: str = "continue",
        check_orphan_expectation_suites: bool = True,
        single_datasource_check: bool = True,
        notify_config: BaseNotifier = None,
        expectation_tags: list[str] = None,
        expectation_params: dict[str, SuiteParameterDict] = {},
        parallel_validation: bool = False,
        max_processes: int = None,
        storage_options: dict[str, any] = {},
    ) -> None:
        """
        Note: These params will be overwritten if your parameters.yml contains hook_options. 

        :param on_failure: Defines what to do when a validation fails. Valid strings are "continue" (failures are \
            visible in the data docs), "raise_fast" (directly raise a SuiteValidationFailure) and "raise_later" (raise \
            a SuiteValidationFailure at the end of the pipeline run, containing information on all failures).
        :param check_orphan_expectation_suites: Boolean to sanity check, if all expectation suites have a \
            corresponding data source.
        :param single_datasource_check: Boolean if each datasource should only be checked once per run (in cases the \
            datasource is used as nodes' input multiple times)
        :param notify_config: Configuration for sending a summarizing notification message about the run, e.g. via email
        :param expectation_params: Optional parameters to be used for parameterized expectations suites.
        :param expectation_tags: List of tags used to filter which expectation suites will be used for validation.
        :param parallel_validation: Boolean to enable parallel validation of datasets. If enabled, each validation will \
            be run in a separate process and the pipeline can continue without waiting. Processes are joined at the end of \
            the pipeline run. NOTICE: This feature is only available for the "raise_later" and "continue" on_failure modes. \
            It ONLY WORKS if the node is run as part of a pipeline run, not in isolation. COPIES ALL INPUT DATA!!!
        :param max_processes: Maximum number of parallel processes to run. Default is the number of CPU cores.
        :param storage_options: Dictionary for configuring temporary storage of checkpoint and validation results \
            Example:
                {
                    "storage_folder": "s3://mybucket/path" or "/local/path",
                    "s3_config": {
                        "client_kwargs": {"endpoint_url": "https://s3.endpoint.com"},
                        "key": "ACCESS_KEY",
                        "secret": "SECRET_KEY"
                    },
                    "clean_on_pipeline_error": True
                }
            - "storage_folder": Path to use for temporary storage; can be an S3 URI or local path.
            - "s3_config": Optional. Required only if using an S3 path. Provides credentials and connection settings.
            - "clean_on_pipeline_error": Whether to clean up stored data if the pipeline fails. Defaults to True.
        """

        self.on_failure = on_failure
        self.check_orphan_expectation_suites = check_orphan_expectation_suites
        self.single_datasource_check = single_datasource_check
        self.expectation_tags = expectation_tags
        self.expectation_params = expectation_params

        self._run_id = None
        self._notifier = notify_config

        self.parallel_validation = parallel_validation
        self.max_processes = max_processes
        self._process_pool = None
        self._manager = None
        self._process_status = None
        self._node_inputs = None
        self._data_catalogs = None

        self._fail_log = []
        self.checkpoint_results = []
        self._datasource_run_counter = {}

        self._validation_runner = None

        self.s3_config = storage_options.get("s3_config")
        self.storage_folder = self._init_storage_folder(
            storage_options.get("storage_folder")
        )
        self.storage_clean_after_error = storage_options.get(
            "clean_on_pipeline_error", True
        )

        self._run_init_assertions()

    def _substitute_kedro_env(self, env: str):
        env = env.lower()
        self.storage_folder = (
            self.storage_folder.replace("{kedro_env}", env)
            if self.storage_folder
            else None
        )

    def _init_storage_folder(self, storage_folder: str) -> Optional[str]:
        if storage_folder:
            # remove trailing whitespace
            storage_folder = storage_folder.strip()

            # handle local paths
            if fsspec.utils.get_protocol(storage_folder) == "file":
                storage_folder = str(Path(storage_folder))
            return storage_folder
        else:
            return None

    def _init_val_attributes(self):
        if self.parallel_validation:
            self._process_pool = multiprocessing.Pool(processes=self.max_processes)
            self._manager = multiprocessing.Manager()
            self._process_status = self._manager.dict()
            self._node_inputs = self._manager.dict()
            self._data_catalogs = self._manager.dict()

            self._fail_log = self._manager.list()
            self.checkpoint_results = self._manager.list()
            self._datasource_run_counter = self._manager.dict()

        self._validation_runner = ValidationRunner(
            on_failure=self.on_failure,
            single_datasource_check=self.single_datasource_check,
            datasource_run_counter=self._datasource_run_counter,
            expectation_tags=self.expectation_tags,
            expectation_params=self.expectation_params,
            run_id=self._run_id,
            notifier=self._notifier,
            fail_log=self._fail_log,
            checkpoint_results=self.checkpoint_results,
            s3_config=self.s3_config,
            storage_folder=self.storage_folder,
        )

    def _run_init_assertions(self):

        assert self.on_failure in ["continue", "raise_fast", "raise_later"], (
            f"Argument 'on_failure' has to be one of "
            f"'continue', 'raise_fast' or 'raise_later', "
            f"but was {self.on_failure}."
        )

        if self.on_failure == "raise_fast":
            assert (
                not self.parallel_validation
            ), "Parallel validation is not supported with 'raise_fast' on_failure mode."

    @hook_impl
    def after_context_created(self, context: KedroContext) -> None:
        config_loader = context.config_loader["parameters"]
        if "hook_options" in config_loader:
            hook_options = config_loader["hook_options"]

            self.on_failure = hook_options.get("on_failure", self.on_failure)
            self.check_orphan_expectation_suites = hook_options.get(
                "check_orphan_expectation_suites", self.check_orphan_expectation_suites
            )
            self.single_datasource_check = hook_options.get(
                "single_datasource_check", self.single_datasource_check
            )
            self.expectation_tags = hook_options.get(
                "expectation_tags", self.expectation_tags
            )
            self.parallel_validation = hook_options.get(
                "parallel_validation", self.parallel_validation
            )
            self.max_processes = hook_options.get("max_processes", self.max_processes)

            notifier_options = hook_options.get("notify_config", {})

            notifier_class = notifier_options.get("class")
            notifier_module = notifier_options.get("module")
            notifier_kwargs = notifier_options.get("kwargs")

            if notifier_class and notifier_module:
                try:
                    module = importlib.import_module(notifier_module)
                    notifier = getattr(module, notifier_class)
                    self._notifier = notifier(**notifier_kwargs)
                except (ImportError, AttributeError) as e:
                    print("Error while importing notifier: ", e)

        kedro_env = (
            context.env 
            or context.config_loader.default_run_env 
            or os.environ.get("KEDRO_ENV", "")
        )
        self._substitute_kedro_env(kedro_env)

        self._init_val_attributes()
        self._run_init_assertions()

    @hook_impl
    def after_catalog_created(
        self,
        catalog: DataCatalog,
        conf_catalog,
        conf_creds,
        feed_dict,
        save_version,
        load_versions,
    ) -> None:
        # Store the session id of the run for the validation result timestamp
        self._run_id = RunIdentifier(run_name="kedro_gx", run_time=None)
        self._validation_runner.run_id = self._run_id
        # Make sure each expectation suite has a corresponding dataset.
        if self.check_orphan_expectation_suites:
            gx = ge.get_context()
            exp_datasets = set(entry.name.split(".")[0] for entry in gx.suites.all())
            catalog_datasets = set(
                entry
                for entry in catalog.list()
                if not entry.startswith("params:") and entry != "parameters"
            )
            orphan_expectation_suites = exp_datasets - catalog_datasets
            if len(orphan_expectation_suites) > 0:
                msg = (
                    f"Found orphan expectation suites not corresponding to any dataset in the catalog: "
                    f"{orphan_expectation_suites}."
                )
                self._validation_runner.publish_failure_msg(msg=msg)

    @hook_impl
    def before_node_run(
        self,
        catalog: DataCatalog,
        inputs: Dict[str, Any],
        node: Node,
    ) -> None:
        """Validate inputs that are supported and have an expectation suite available."""
        if (
            self.before_node_run
            and base_ge_folder_exists(verbose=False)
            and location_is_kedro_root_folder()
        ):

            if not self.parallel_validation:
                self._validation_runner.catalog = catalog
                self._validation_runner.data = inputs
                self._validation_runner._run_validation()
                return

            name = node.name + "==" + "+".join(inputs.keys())
            self._data_catalogs[name] = deepcopy(catalog)
            self._node_inputs[name] = deepcopy(inputs)

            self._process_pool.apply_async(
                KedroExpectationsHooks.create_and_run_validation_runner,
                args=(
                    self._data_catalogs,
                    self._node_inputs,
                    self.on_failure,
                    self.single_datasource_check,
                    self._datasource_run_counter,
                    self.expectation_tags,
                    self.expectation_params,
                    self._run_id,
                    self._notifier,
                    self._fail_log,
                    self.checkpoint_results,
                    self._process_status,
                    name,
                    self.s3_config,
                    self.storage_folder,
                ),
            )
            self._process_status[name] = "queued"
            print("Queued process: ", name, flush=True)

    @hook_impl
    def after_pipeline_run(
        self, run_params: Dict, run_result, pipeline, catalog: DataCatalog
    ):
        if self.parallel_validation:

            print(
                "Running processes: ",
                [id for id, stat in self._process_status.items() if stat == "running"],
                flush=True,
            )

            print(
                "Queued processes: ",
                [id for id, stat in self._process_status.items() if stat == "queued"],
                flush=True,
            )

            self._process_pool.close()
            self._process_pool.join()

        self._validation_runner.send_notification()

        # finally raise Exception if validations failed and option is set
        if self._fail_log:
            if self.on_failure == "raise_later":
                raise SuiteValidationFailure(
                    "During pipeline run one or more expectation suite validations failed:\n"
                    + "\n".join(self._fail_log)
                    + "\n"
                )
            else:
                print(
                    "During pipeline run one or more expectation suite validations failed:\n"
                    + "\n".join(self._fail_log)
                    + "\n"
                )

    @hook_impl
    def on_pipeline_error(self):
        if self.storage_clean_after_error:
            storage_location = self.storage_folder
            if storage_location:
                delete_checkpoints(storage_location, self.s3_config)

    @staticmethod
    def create_and_run_validation_runner(
        catalogs: multiprocessing.managers.DictProxy,
        node_inputs: multiprocessing.managers.DictProxy,
        on_failure: str,
        single_datasource_check: bool,
        datasource_run_counter: dict,
        expectation_tags: list[str],
        expectation_params: dict[str, SuiteParameterDict],
        run_id: RunIdentifier,
        notifier: BaseNotifier,
        fail_log: list[str],
        checkpoint_results: list[KedroExpectationsCheckpointResult],
        task_status: dict,
        task_name: str,
        s3_config: dict[str, str],
        storage_folder: str,
    ):
        catalog = catalogs.pop(task_name)
        inputs = node_inputs.pop(task_name)

        runner = ValidationRunner(
            on_failure=on_failure,
            single_datasource_check=single_datasource_check,
            datasource_run_counter=datasource_run_counter,
            expectation_tags=expectation_tags,
            expectation_params=expectation_params,
            run_id=run_id,
            notifier=notifier,
            fail_log=fail_log,
            checkpoint_results=checkpoint_results,
            catalog=catalog,
            inputs=inputs,
            s3_config=s3_config,
            storage_folder=storage_folder,
        )
        try:
            task_status[task_name] = "running"
            print("Running process: ", task_name, flush=True)
            runner._run_validation()
        finally:
            task_status[task_name] = "finished"
            print("Finished process: ", task_name, flush=True)


class ValidationRunner:

    def __init__(
        self,
        on_failure: str,
        single_datasource_check: bool,
        datasource_run_counter: dict,
        expectation_tags: list[str],
        expectation_params: dict[str, dict[any, any]],
        run_id: RunIdentifier,
        notifier: BaseNotifier,
        fail_log: list[str],
        checkpoint_results: list[KedroExpectationsCheckpointResult],
        catalog: DataCatalog = None,
        inputs: Dict[str, Any] = None,
        s3_config: Dict[str, str] = None,
        storage_folder: str = None,
    ):

        self.catalog = catalog
        self.data = inputs
        self.on_failure = on_failure
        self.single_datasource_check = single_datasource_check
        self.datasource_run_counter = datasource_run_counter
        self.expectation_tags = expectation_tags
        self.expectation_params = expectation_params
        self.run_id = run_id
        self.notifier = notifier
        self.fail_log = fail_log
        self.checkpoint_results = checkpoint_results
        self.s3_config = s3_config
        self.storage_folder = storage_folder

    def _run_validation(self) -> None:
        ge_context = ge.get_context()
        for key, value in self.data.items():
            if (
                self.single_datasource_check
                and self.datasource_run_counter.get(key, 0) > 0
            ):
                # skip each further check after the first
                continue
            self.datasource_run_counter[key] = (
                self.datasource_run_counter.get(key, 0) + 1
            )
            catalog_key = key.replace(":", "__").replace(".", "__")
            adjusted_key = dot_to_underscore(key)

            if isinstance(
                getattr(self.catalog.datasets, catalog_key), PartitionedDataset
            ):
                partitions = cast(Dict[str, Callable], value)
            else:
                partitions = {adjusted_key: lambda: value}

            for casted_key, casted_value in partitions.items():
                # Looking for a general expectation
                current_key = adjusted_key
                all_expectations = get_all_expectations(
                    ge_context=ge_context, adjusted_key=current_key
                )
                ge_adjusted_key = current_key

                # Looking for a specific expectation
                if (
                    not all_expectations and casted_key != adjusted_key
                ):  # partition dataset
                    adjusted_key_pt2 = dot_to_underscore(casted_key)
                    current_key = os.path.join(adjusted_key, adjusted_key_pt2)
                    all_expectations = get_all_expectations(
                        ge_context=ge_context, adjusted_key=current_key
                    )
                    ge_adjusted_key = current_key + "." + adjusted_key_pt2

                # filter expactations for given tag
                expectations_filtered = []
                if self.expectation_tags is not None:
                    for expectation in all_expectations:
                        suite_name = get_suite_name(expectation, ge_adjusted_key)
                        file = ge_context.suites.get(suite_name)
                        if set(self.expectation_tags) & set(file["meta"]["tags"]):
                            expectations_filtered.append(expectation)

                    if not expectations_filtered:
                        print(
                            f"No expectation suite for tags {self.expectation_tags}.",
                            "Validation will be skipped!",
                        )
                else:
                    expectations_filtered = all_expectations

                for exp_file in expectations_filtered:
                    suite_name = get_suite_name(exp_file, ge_adjusted_key)
                    exp_params = self.expectation_params.get(suite_name, {})
                    value = casted_value()
                    if isinstance(value, PandasDataFrame):
                        result = validate(
                            ge_context,
                            dataset_name=casted_key,
                            suite_name=suite_name,
                            validation_df=value,
                            exp_params=exp_params,
                            run_id=self.run_id,
                        )
                        suite_name = result.name.replace("_kedro_checkpoint", "")
                        # for some reason the exception info is not pickleable
                        # we don't need it for our purposes, so just set it to an empty dict
                        for val_res in result.run_results.values():
                            for r in val_res.get("results", []):
                                r["exception_info"] = {}

                        kedro_gx_result = KedroExpectationsCheckpointResult(
                            suite_name, result.run_results, result.success
                        )
                        self.checkpoint_results.append(kedro_gx_result)
                    else:
                        raise SuiteValidationFailure(
                            f"Dataset {adjusted_key} is no Pandas DataFrame and not supported by Kedro Expectations"
                        )
                    if not result.success:
                        msg = f"Suite {suite_name} for DataSet {current_key} failed!"
                        self.publish_failure_msg(
                            msg=msg,
                        )
                if not all_expectations:
                    print(
                        f'No expectation suite was found for "{key}".',
                        "Validation will be skipped!",
                    )

    def publish_failure_msg(self, msg: str):
        self.fail_log.append(msg)
        if self.on_failure == "raise_fast":
            self.send_notification()
            raise SuiteValidationFailure(msg)

    def send_notification(self):

        # Convert Multiprocessing List to python list. This is necessary for pickling
        self.checkpoint_results = list(self.checkpoint_results)

        # Default to no storage/cumulation
        email_setting = os.environ.get("KEDRO_GX_NOTIFICATION_SETTING", "MAIL").strip()

        # summarize the successful and failed validations for email report
        failed_validation_results: list[ExpectationValidationResult] = []
        failed_expectation_suite_results: dict[
            ExpectationSuiteIdentifier, ExpectationSuiteValidationResult
        ] = {}
        successful_expectations = 0
        evaluated_expectations = 0
        # payload = {"update_data_docs": {"class": "UpdateDataDocsAction"}}

        if email_setting == CONSTANT_EMAIL_SETTING_STORE:
            if not self.storage_folder:
                print("ERROR: storage_folder is unset, cannot store checkpoints!")
                exit(0)

            store_checkpoints(
                self.storage_folder, list(self.checkpoint_results), self.s3_config
            )

            # Return after Storing
            return

        if email_setting == CONSTANT_EMAIL_SETTING_CUMULATE:

            stored_checkpoints = load_checkpoints(
                self.storage_folder, self.s3_config
            )
            # inplace ...
            stored_checkpoints.extend(self.checkpoint_results)
            self.checkpoint_results = stored_checkpoints

            delete_checkpoints(self.storage_folder, self.s3_config)

            # go on noramlly after loading additional checkpoints

        if self.notifier is None or not self.notifier.will_notify(
            all(check.success for check in self.checkpoint_results)
        ):
            return

        for checkpoint_result in self.checkpoint_results:
            suite_name = checkpoint_result.suite_name
            dataset_name, _ = split_suite_name(suite_name)

            for (
                validation_result_id,
                validation_result,
            ) in checkpoint_result.run_results.items():
                validation_result: ExpectationSuiteValidationResult = (
                    checkpoint_result.run_results[validation_result_id]
                )

                if not validation_result.success:
                    failed_expectation_suite_results[validation_result_id] = (
                        validation_result
                    )

                    failed_validation_results.extend(
                        [
                            result
                            for result in validation_result.results
                            if not result.success
                        ]
                    )
                successful_expectations += validation_result.statistics[
                    "successful_expectations"
                ]
                evaluated_expectations += validation_result.statistics[
                    "evaluated_expectations"
                ]

        if evaluated_expectations == 0:
            success_percent = None
        else:
            success_percent = successful_expectations / evaluated_expectations * 100

        # create a summarizing validation result
        summary_validation_result = ExpectationSuiteValidationResult(
            suite_name="Summary_Expectation_Suite",
            success=len(failed_validation_results) == 0,
            results=failed_validation_results,
            statistics={
                "successful_expectations": successful_expectations,
                "evaluated_expectations": evaluated_expectations,
                "success_percent": success_percent,
                "unsuccessful_expectations": evaluated_expectations
                - successful_expectations,
            },
            meta={
                "expectation_suite_name": "Summary_Expectation_Suite",
                "batch_kwargs": {"data_asset_name": "All"},
                "run_id": self.run_id,
            },
        )

        # create a summarizing checkpoint result
        checkpoint_result = CheckpointResult(
            run_id=self.run_id,
            run_results={
                ValidationResultIdentifier(
                    expectation_suite_identifier=ExpectationSuiteIdentifier(
                        "Summary_Expectation_Suite"
                    ),
                    run_id=self.run_id,
                    batch_identifier=f"summary",
                ): summary_validation_result,
                **failed_expectation_suite_results,
            },
            checkpoint_config=Checkpoint(
                name=self.notifier.subject,  # define this here, as it will be the subject of the msg (e.g. email)
                validation_definitions=[],
            ),
        )

        self.notifier.run(checkpoint_result=checkpoint_result)
