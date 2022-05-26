"""Primary class defining conversion of experiment-specific behavior."""
from pathlib import Path

import numpy as np
import pandas as pd
from pymatreader import read_mat

from pynwb import NWBFile
from nwb_conversion_tools.basedatainterface import BaseDataInterface
from nwb_conversion_tools.utils.types import FolderPathType


class Embargo22ABehaviorInterface(BaseDataInterface):
    """My behavior interface docstring"""

    def __init__(self, session_path: FolderPathType):
        super().__init__(session_path=session_path)

    def get_metadata(self):
        # Automatically retrieve as much metadata as possible

        empty_metadata = dict()
        return empty_metadata

    def run_conversion(self, nwbfile: NWBFile, metadata: dict):

        session_path = Path(self.source_data["session_path"])
        file_path = session_path / "M22D20210127R0TS.mat"

        data_simple = read_mat(str(file_path))
        trial_structure = data_simple["TS"]

        # Mappings
        header = trial_structure["Header"]
        definitions = header["DEF"]
        number_to_outcome_map = {number: outcome for outcome, number in definitions["OUTCOME"].items()}

        type_condition_to_description = {0: "blank", 1: "target", 2: "visual_stimulus"}
        conditions = header["Conditions"]
        conditions_type = [type_condition_to_description[type_cond] for type_cond in conditions["TypeCond"]]
        current_condition_to_description = {cond + 1: description for cond, description in enumerate(conditions_type)}

        # Trial data
        trial_data = trial_structure["Trial"]
        df_trial_data = pd.DataFrame(trial_data)
        columns_with_structure = [
            "Database",
            "Graphics",
            "Events",
            "ServerParams",
            "TTLCfg",
            "FPPos",
            "BKColor",
            "FPColor",
        ]
        df_trial_data = (
            df_trial_data.replace(-1, np.nan)  # Replace -1 by NaN
            .dropna(axis=1, how="all")  # Drop columns with only NaN
            .sort_values(by="TrialNum")  # Sort by the trial number
            .drop(columns=["TrialNum"])  # Drop trial number
            .drop(columns=columns_with_structure)  # Drop columns with complex structure
        )

        # Remove columns with only one value
        all_columns = set(df_trial_data.columns.values)
        single_value_columns = [c for c in all_columns if len(df_trial_data[c].unique()) == 1]
        columns_with_muliple_values = all_columns.difference(single_value_columns)
        df_trial_data = df_trial_data[columns_with_muliple_values]

        # Add information to trial data
        df_trial_data["Outcome"] = [number_to_outcome_map[outcome].lower() for outcome in df_trial_data["Outcome"]]
        df_trial_data["condition type"] = [
            current_condition_to_description[CurrCond] for CurrCond in df_trial_data["CurrCond"]
        ]

        # Time in seconds
        time_columns = [column for column in df_trial_data.columns if "Time" in column and "Now" not in column]
        for column in time_columns:
            df_trial_data[column] = df_trial_data[column] / 1000.0

        # Order them by average distance from trial start
        df_aligned = df_trial_data[time_columns].sub(df_trial_data.TimeTrialStart, axis=0)
        ordered_time_columns = df_aligned.mean(axis=0).sort_values().index.to_list()

        # Order the rest alphabetically
        all_columns = set(df_trial_data.columns.values)
        non_time_columns = all_columns.difference(set(time_columns))
        all_columns = set(df_trial_data.columns.values)
        non_time_columns = list(all_columns.difference(set(time_columns)))
        non_time_columns.sort()
        ordered_columns = ordered_time_columns + non_time_columns

        df_trial_data = df_trial_data[ordered_columns]

        # Re-name
        df_trial_data.rename(
            columns={"TimeTrialStart": "start_time", "TimeTrialEnd": "stop_time"},
            inplace=True,
        )
        for column in all_columns:
            nwbfile.add_trial_column(name=column, description=column)  # To-do add column description
        # Add the trials table
        rows_as_dicts = df_trial_data.T.to_dict().values()
        [nwbfile.add_trial(**row_dict) for row_dict in rows_as_dicts]
