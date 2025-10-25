[![Latest Release](https://gitlab.com/anacision/kedro-expectations/-/badges/release.svg)](https://gitlab.com/anacision/kedro-expectations)
[![PyPI - Version](https://img.shields.io/pypi/v/kedro-expectations?label=pypi%20version&color=FEC900)](https://pypi.org/project/kedro-expectations/)
[![Pipeline Status](https://gitlab.com/anacision/kedro-expectations/badges/main/pipeline.svg)](https://gitlab.com/anacision/kedro-expectations)
[![Coverage](https://gitlab.com/anacision/kedro-expectations/badges/main/coverage.svg)](https://gitlab.com/anacision/kedro-expectations)
[![GitLab Last Commit](https://img.shields.io/gitlab/last-commit/anacision%2Fkedro-expectations)](https://gitlab.com/anacision/kedro-expectations)
[![GitLab Last Commit](https://img.shields.io/gitlab/contributors/anacision%2Fkedro-expectations)](https://gitlab.com/anacision/kedro-expectations)
[![Python version](https://img.shields.io/pypi/pyversions/kedro-expectations?color=FEC900)](https://pypi.org/project/kedro-expectations/)
[![License](https://img.shields.io/gitlab/license/anacision%2Fkedro-expectations?color=FEC900)](https://opensource.org/license/mit)
[![Maintainers](https://img.shields.io/badge/maintainers-anacision%20GmbH-%23FEC900.svg)](https%3A%2F%2Fanacision.de)

---

<p align="left">
  <img width=160 height=160 src="./images/logo.svg">
</p>


# kedro-expectations
A tool to better integrate Kedro and Great Expectations

## Introduction

Kedro Expectations is a tool designed to make the use of Great Expectations (GX, a data validation tool) within Kedro data science pipelines easier. It is composed of a couple of commands and a hook, allowing the user to create expectation suites and run validations on the Kedro DataCatalog on-the-fly. Check out our [blog post](https://medium.com/@anacision/introducing-kedro-expectations-bridging-data-validation-and-monitoring-in-data-science-pipelines-e6cde6e98349) for a deeper dive into the workings and motivation behind this project!

## Features

- ⏳ Initialization of GX without having to worry about datasources
- 🎯 Creation of [GX suites](https://docs.greatexpectations.io/docs/core/define_expectations/organize_expectation_suites) automatically, using the Data Assistant profiler
- 🚀 Running validations within the Kedro pipeline on-the-fly
- ⚡ Optional: Parallel running validations to prevent blocking the Kedro pipeline
- 🔔 Custom notification setup to keep up-to-date about validations

---

## Installation

You can install the plugin via PyPI:

```bash
pip install kedro-expectations
```

## Usage

### CLI Usage

As a first step to use the Kedro Expectations run the following command to create an expectation suite for a given Kedro data set:

```bash
kedro expectations create-suite
```

You are guided by a dialog and the script automatically analyzes the dataset using a DataAssistant profiler. It is possible to create expectation suites for Non-spark dataframe objects (there is no need to worry about the file type since Kedro Expectations utilizes the information from the Kedro data catalog) and partitioned datasets. Within partitioned datasets, it is possible to create generic expectations, meaning all the partitions will use that expectation, or specific expectations, meaning only the specified partition will use the generated expectation.

Besides creating the expectation suite, the command also creates the base GX folder and the datasources / assets it needs to run Great Expectations, given that they don't exist already.


### Hook Usage

In order to enable the hook capabilities you only need to register it in the settings.py file inside your kedro project.

(inside src/your_project_name/settings.py)
```python
from kedro_expectations import KedroExpectationsHooks

HOOKS = (KedroExpectationsHooks(
            on_failure="raise_fast",
            ),
        )
```

There you can specifiy the parameters that you want to start your hook with.
**Additionally:** You can specifiy the `hook_options` in your *parameters.yml* (conf/base/parameters.yml) that is generated automatically by kedro. These options are preferred over the ones specified in the settings.py registration and will override them once kedro starts up!

```yml
hook_options:
  on_failure: raise_later
  parallel_validation: True
  check_orphan_expectation_suites: True
  single_datasource_check: True
  expectation_tags: null
  notify_config: 
    module: kedro_expectations.notification
    class: EmailNotifier
    kwargs:
      recipients: ["john.doe@anacision.de"]
      smtp_address: smtp.testserver.com
      smtp_port: 123
      sender_login: dummylogin
      sender_password: dummypassword
      security_protocol: None
```


#### Parameters

The hook allows for different parameters in order to customize it to your desired behavior.

**on_failure**: is a parameter added to give more control over the pipeline. That way it is possible to define, if an expectation's validation failure breaks the pipeline run immediately (`on_failure="raise_fast"`), at the end (`on_failure="raise_later`) or not at all (`on_failure="continue"`). Its default value is "continue".

**parallel_validation**: is a parameter to control whether expectation validations are run in a seperate process or not. This is useful because some validations may take a long time and the result might not be relevant for the further continuation of the pipeline, thus a parallel process validation allows the kedro pipeline to continue running. Logically, the option is NOT available for the `on_failure=raise_fast` mode. 

**max_processes**: Maximum number of processes that can run concurrently for the parallel validation mode. Defaults to the number of CPU cores in your system.

**check_orphan_expectation_suites**: controls whether to check (and potentially raise errors) for defined expectation suites that do not have a corresponding data source.

**single_datasource_check**: controls whether the same datasource is validated every time it is used in a kedro pipeline or only at its first encounter.

**expectation_tags**: List of tags used to filter which expectation suites will be used for validation.

### Notification

With the `notify_config` argument you can set up automatic notifications about the validation run. It uses the GX checkpoint actions to render and send the notification. Currently only notification via email is supported. To set it up, add the following argument to the `KedroExpectationsHooks` object within `settings.py` and modify the addresses and credentials according to your SMTP server and needs. Alternatively you can use the *parameters.yml* like shown in the example above.

```python
from kedro_expectations import KedroExpectationsHooks
from kedro_expectations.notification import EmailNotifier

HOOKS = (KedroExpectationsHooks(
            notify_config=EmailNotifier(
              recipients=["john_doe@nobody.io", ],
              sender_login="login",
              sender_password="password",
              smtp_address="smtp.address",
              smtp_port="465"
              )
            ),
        )
```

---

## Example

To make things clearer, the following example will walk you through usage of the plugin, from setup to creating an expectation suite to finally running the pipeline. It was done using the [Spaceflights Starter](https://github.com/ProjetaAi/projetaai-starters/tree/main/for_projetaai/project/partitioned_projetaai) project provided by kedro.

To start using the plugin, make sure you are in your project's root folder and your pipeline is executing correctly.

Considering you have the plugin installed and the conditions right above are true, the main steps are:
- Create one or more suites depending on your needs
- Make sure to insert the KedroExpectationsHooks in your project settings' HOOKS list
- Execute the Kedro Pipeline as usual

### Suite Creation

You can start using the plugin directly by running the command for creating an expectation suite: "kedro expectations create-suite". 
You will be prompted to choose between (1) suites for generic datasets and (2) suites for partitioned datasets. In this example we will choose (1) to create a generic dataset.

<p align="center">
  <img src="./images/1_createsuite.png">
</p>

After that, we will be asked to enter the dataset name. Please enter the exact name of your dataset as defined in the `catalog.yml` of your kedro project. In the next step, you can freely choose a name for the expectation suite that is about to be created.
The plugin will load the dataset and display all its available columns. Now you can choose which columns to exclude from your new expectation suite by typing each name one by one into the terminal. If you want to include every column, just input '0' directly to proceed with the creation.

<p align="center">
  <img src="./images/2_createsuite.png">
</p>

After this step is done, the plugin will automatically create an expectation suite for the specified dataset based on the data currently present inside it.

<p align="center">
  <img src="./images/3_createsuite.png">
</p>

You should be able to find this newly generated expectation suite in your project structure under gx/expectations/"dataset_name"/"ex_suite_name".json.

<p align="left">
  <img src="./images/4_createsuite.png">
</p>

### Adding the Hook

Now, to be able to test, we only need to add a few lines of code in our settings.py file as shown [above](README.md#hook-usage)

For more information about the functionality of Kedro Hooks, please refer to the [Kedro Hook Documentation](https://kedro.readthedocs.io/en/stable/hooks/introduction.html)

### Running the Kedro project

After adding the Hook there is no more extra step required. You can simply run the project by using the default "kedro run" command. Whenever a dataset with an existing expectation suite is called by the pipeline, kedro-expectations will validate it, add the results to the data_docs and (optionally) notify you.

<p align="center">
  <img src="./images/5_run.png">
</p>

---

# Tests

to run tests install pytest and call
`pytest --cov=kedro_expectations/`

## Contribution

Based on work from Joao Gabriel Pampanin de Abreu. Extended and updated by anacision GmbH since 2023.
For details about how to contribute or to report issues, reach out to us via tech@anacision.de or to any of the people listed below.

Main Developers:
- Marcel Beining (marcel.beining@anacision.de)
- Pascal Schmidt (pascal.schmidt@anacision.de)

---


# License

This project is licensed under the **MIT License**.  
You are free to use, modify, and distribute the code under the terms of the MIT license.  
See the [LICENSE](./LICENSE) file for details.

## Third-Party Code

This project includes source files copied from:

- **[Great Expectations](https://github.com/great-expectations/great_expectations)** — licensed under the **Apache License 2.0**

These files are located in the `kedro_expectations/assistant/experimental` directory and were copied from version `v1.5.0`,  
prior to the deprecation and removal of the functionality in the original project.  
They retain their original Apache 2.0 license and are not relicensed under MIT.

For the full license text, see the [APACHE_LICENSE](./kedro_expectations/assistant/experimental/APACHE_LICENSE.txt) file.