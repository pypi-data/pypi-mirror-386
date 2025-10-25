import glob
import json
import os
from enum import Enum

from .experimental.rule_based_profiler.rule import Rule


class DATASET_TYPE(Enum):
    FULL = 1
    PARTITIONED = 2


def get_onboarding_rules(dataset_type: DATASET_TYPE) -> dict[str, Rule]:
    base_path = os.path.dirname(__file__)
    json_files_in_directory = glob.glob(os.path.join(base_path, "*.json"))

    # Remove dataset type specific rules that do not count
    if dataset_type == DATASET_TYPE.FULL:
        json_files_in_directory = [
            file
            for file in json_files_in_directory
            if not file.endswith("_partitioned.json")
        ]
    else:
        json_files_in_directory = [
            file for file in json_files_in_directory if not file.endswith("_full.json")
        ]

    rules = {}
    for json_file in json_files_in_directory:
        with open(json_file, "r") as fh:
            rule_dict = json.load(fh)
            rule_name = json_file.replace(".json", "")
            rules[rule_name] = Rule(name=rule_name, **rule_dict)
    return rules
