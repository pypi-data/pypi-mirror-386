import click
import os
from typing import Dict, cast, Callable
import great_expectations as ge
import pandas as pd
from great_expectations import ExpectationSuite
from kedro.framework.session import KedroSession
from kedro_datasets.partitions import PartitionedDataset

from kedro_expectations.assistant.rules import DATASET_TYPE

from kedro_expectations.utils import (
    dot_to_underscore,
    populate_new_suite,
    is_dataset_in_catalog,
    choose_valid_suite_name,
    choose_valid_dataset_name,
)


@click.command()
@click.option("--env", default=None, help="The respective Kedro environment to use")
def create_suite(env):
    # how to get cli args in here
    start_suite_creation(ge_context=ge.get_context(mode="file"), env=env)


def start_suite_creation(ge_context, env=None):
    click.echo("Type 1 if you want to create a suite for a generic dataset")
    click.echo("Type 2 if you want to create a suite for a Partitioned dataset")
    option = click.prompt("", type=int)

    if option == 1:
        click.echo("Type the dataset name as it is on the DataCatalog")
        dataset_name = click.prompt("", type=str)

        click.echo("Type the desired name for the expectation suite")
        suite_name = choose_valid_suite_name()

        project_path = os.getcwd()
        with KedroSession.create(
            project_path=project_path,
            env=env,
        ) as session:
            kedro_context = session.load_context()
            catalog = kedro_context.catalog
            if is_dataset_in_catalog(dataset_name, catalog) is True:
                adjusted_dataset_name = dot_to_underscore(dataset_name)
                expectation_suite_name = adjusted_dataset_name + "." + suite_name
                ge_context.suites.add(
                    ExpectationSuite(
                        expectation_suite_name,
                    )
                )
                input_data = catalog.load(dataset_name)
                populate_new_suite(
                    input_data, expectation_suite_name, dataset_type=DATASET_TYPE.FULL
                )

    elif option == 2:

        project_path = os.getcwd()
        with KedroSession.create(project_path=project_path, env=env) as session:
            kedro_context = session.load_context()
            catalog = kedro_context.catalog

            partitioned_items = []
            for catalog_item in catalog.list(regex_search="^(?!params:).+"):
                if isinstance(
                    getattr(catalog.datasets, catalog_item), PartitionedDataset
                ):
                    partitioned_items.append(catalog_item)

        if partitioned_items:
            click.echo("\nType 1 if you want to create a generic expectation")
            click.echo("Type 2 if you want to create an specific expectation")
            option = click.prompt("", type=int)

            if option == 1:
                click.echo("Type the dataset name as it is on the DataCatalog")
                dataset_name = choose_valid_dataset_name(catalog)

                click.echo("Type the desired name for the expectation suite")
                suite_name = choose_valid_suite_name()

                project_path = os.getcwd()
                with KedroSession.create(project_path=project_path) as session:
                    kedro_context = session.load_context()
                    catalog = kedro_context.catalog
                    if is_dataset_in_catalog(dataset_name, catalog) is True:
                        adjusted_dataset_name = dot_to_underscore(dataset_name)
                        expectation_suite_name = (
                            adjusted_dataset_name + "." + suite_name
                        )
                        ge_context.suites.add(
                            ExpectationSuite(
                                expectation_suite_name,
                            )
                        )
                        input_data = catalog.load(dataset_name)
                        partitions = cast(Dict[str, Callable], input_data)
                        validation_df = pd.DataFrame()

                        for casted_key, casted_value in partitions.items():
                            validation_df = pd.concat(
                                [validation_df, casted_value()],
                                ignore_index=True,
                                sort=False,
                            )
                            if len(validation_df.index) >= 100000:
                                print(
                                    "CAUTION! "
                                    "The loading of the whole partitioned dataframe reached above 100000 rows. "
                                    "Skipping further loading to avoid memory problems."
                                )

                        populate_new_suite(
                            validation_df,
                            expectation_suite_name,
                            dataset_type=DATASET_TYPE.PARTITIONED,
                        )
            elif option == 2:
                click.echo("Type the dataset name as it is on the DataCatalog")
                dataset_name = choose_valid_dataset_name(catalog)

                click.echo(
                    "Type the specific partition name you want to create an Expectation Suite for"
                )
                desired_part = click.prompt("", type=str)

                click.echo("Type the desired name for the expectation suite")
                suite_name = choose_valid_suite_name()

                project_path = os.getcwd()
                with KedroSession.create(project_path=project_path) as session:
                    kedro_context = session.load_context()
                    catalog = kedro_context.catalog
                    if is_dataset_in_catalog(dataset_name, catalog) is True:
                        adjusted_input_pt1 = dot_to_underscore(dataset_name)
                        adjusted_input_pt2 = dot_to_underscore(desired_part)
                        expectation_suite_name = (
                            adjusted_input_pt1
                            + "."
                            + adjusted_input_pt2
                            + "."
                            + suite_name
                        )
                        ge_context.suites.add(
                            ExpectationSuite(
                                expectation_suite_name,
                            )
                        )
                        input_data = catalog.load(dataset_name)
                        partitions = cast(Dict[str, Callable], input_data)

                        try:
                            validation_df = partitions[desired_part]()
                            print(validation_df.shape)
                            populate_new_suite(
                                validation_df,
                                expectation_suite_name,
                                dataset_type=DATASET_TYPE.PARTITIONED,
                            )
                        except KeyError:
                            print(
                                f"""
                                The partition {desired_part} does not exit!
                                Suite was not populated.
                                """
                            )
            else:
                print("\n\nThe number typed is invalid. Aborting!")
        else:
            print("\n\nThere are no partitioned datasets registered in your catalog")
    else:
        print("\n\nThe number typed is invalid. Aborting!")
