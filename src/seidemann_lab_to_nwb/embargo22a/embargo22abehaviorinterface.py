"""Primary class defining conversion of experiment-specific behavior."""
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio

from pynwb import NWBFile
from nwb_conversion_tools.basedatainterface import BaseDataInterface
from nwb_conversion_tools.utils.types import FolderPathType
from ndx_events import LabeledEvents
from nwb_conversion_tools.tools.nwb_helpers import get_module


class Embargo22ABehaviorInterface(BaseDataInterface):
    """My behavior interface docstring"""

    def __init__(self, session_path: FolderPathType):
        super().__init__(session_path=session_path)
        self.session_path = Path(self.source_data["session_path"])

    def get_metadata(self):
        # Automatically retrieve as much metadata as possible

        empty_metadata = dict()
        return empty_metadata

    def run_conversion(self, nwbfile: NWBFile, metadata: dict):

        file_path = self.session_path / "M22D20210127R0TS.mat"
        data_simple = sio.loadmat(str(file_path), simplify_cells=True)
        trial_structure = data_simple["TS"]

        self.add_events(nwbfile, trial_structure)
        self.add_trials(nwbfile, trial_structure)

    def add_trials(self, nwbfile, trial_structure):

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
            df_trial_data.drop(columns=columns_with_structure)  # Drop columns with complex structure
            .replace(-1, np.nan)  # Replace -1 by NaN
            .dropna(axis=1, how="all")  # Drop columns with only NaN
            .sort_values(by="TrialNum")  # Sort by the trial number
            .drop(columns=["TrialNum"])  # Drop trial number
        )

        # Remove columns with only one value
        all_columns = set(df_trial_data.columns.values)
        single_value_columns = [c for c in all_columns if len(df_trial_data[c].unique()) == 1]
        df_trial_data = df_trial_data.drop(columns=single_value_columns)

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

        # Re-name for complying with `add_trial` function.
        df_trial_data.rename(
            columns={"TimeTrialStart": "start_time", "TimeTrialEnd": "stop_time"},
            inplace=True,
        )

        columns_to_add = [column for column in all_columns if column not in ["TimeTrialStart", "TimeTrialEnd"]]

        for column in columns_to_add:
            nwbfile.add_trial_column(name=column, description=column)  # To-do add column description

        # Add the trials table
        rows_as_dicts = df_trial_data.T.to_dict().values()
        [nwbfile.add_trial(**row_dict) for row_dict in rows_as_dicts]

    def add_events(self, nwbfile, trial_structure):

        # Mappings
        header = trial_structure["Header"]
        definitions = header["DEF"]
        number_to_event_definition_map = {number: outcome for outcome, number in definitions["EVENT"].items()}

        # Extract and process the data.
        file_path_events = self.session_path / "events.csv"
        df_events = pd.read_csv(file_path_events)
        df_events["event_type"] = [number_to_event_definition_map[number].lower() for number in df_events["Type"]]
        df_events["event"] = [number_to_event_definition_map[number].lower() for number in df_events["EventID"]]
        df_events.drop(columns=["EventID", "Type", "TrialNum"], inplace=True)
        df_events.rename(columns={"Timestamp": "timestamps"}, inplace=True)

        # For this conversion the types of events are the following
        # ["type_eye_state", "type_protocol_state", "type_new_trial", "type_oi_state", "type_reward_state"]
        event_type_array = df_events.event_type.unique()
        behavior_module = get_module(nwbfile, "behavior")  # Not clear yet if all those types should go into behavior

        for event_type in event_type_array:
            df_event_type = df_events.query(f"event_type=='{event_type}'")
            timestamps = df_event_type.timestamps.to_numpy()
            labels = df_event_type.event.unique()
            labels.sort()
            label_to_postion = {label: position for position, label in enumerate(labels)}
            data = [label_to_postion[label] for label in df_event_type.event]

            events = LabeledEvents(
                name=event_type,
                description=event_type,  # Look for descriptions
                timestamps=timestamps,
                data=data,
                labels=labels,
            )
            behavior_module.add(events)
