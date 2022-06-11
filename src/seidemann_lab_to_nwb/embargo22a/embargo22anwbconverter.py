"""Primary NWBConverter class for this dataset."""
from pathlib import Path
from dateutil import parser
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from pymatreader import read_mat

from nwb_conversion_tools import NWBConverter, Suite2pSegmentationInterface

from seidemann_lab_to_nwb.embargo22a import Embargo22ABehaviorInterface
from numpymemmapimaginginterface import NumpyMemmapImagingInterface


class Embargo22ANWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        Imaging=NumpyMemmapImagingInterface,
        Suit2P=Suite2pSegmentationInterface,
        Behavior=Embargo22ABehaviorInterface,
    )

    def __init__(self, source_data: dict):
        super().__init__(source_data=source_data)
        self.session_path = Path(self.data_interface_objects["Behavior"].source_data["session_path"])
        self.add_time_stamps_to_imaging_extractor()

    def add_time_stamps_to_imaging_extractor(self):

        # Get the smallest timestamp
        file_path_events = self.session_path / "events.csv"
        smallest_timestamp = pd.read_csv(file_path_events).Timestamp.min()

        file_path = self.session_path / "M22D20210127R0Data2P20201001.mat"
        data_simple = read_mat(
            str(file_path), variable_names=["TS"], ignore_fields=["Events", "nTrial", "FileName", "Sync", "Header"]
        )
        trial_structure = data_simple["TS"]

        # Trial data
        trial_data = trial_structure["Trial"]
        df_valid_trials = pd.DataFrame(trial_data)
        df_valid_trials = df_valid_trials.query("FlagOIBLK == 1") # Flag indicating imaging extraction

        optical_imaging_trigger_time = df_valid_trials["TimeOITrigger"]  # time to triger imaging system

        frames_per_trial = 75
        sampling_frequency = 30.0
        sampling_period = 1.0 / sampling_frequency

        timestamps = []
        for start_time in optical_imaging_trigger_time:
            start = start_time
            stop = start + sampling_period * frames_per_trial
            timestamps.append(np.linspace(start=start, stop=stop, num=frames_per_trial))

        timestamps = np.concatenate(timestamps)
        
        timestamps /= 1e3  # Transform to seconds
        timestamps -= smallest_timestamp  # Center with respect to the smallest timestamps in the data

        
        # Add them to imaging extractor
        imaging_interface = self.data_interface_objects["Imaging"]
        imaging_extractor = imaging_interface.imaging_extractor
        imaging_extractor.set_times(times=timestamps)
        
        del data_simple

    def get_metadata(self):
        metadata = super().get_metadata()

        # Only the more complicated file has the datetime
        file_path = self.session_path / "M22D20210127R0Data2P20201001.mat"

        data_simple = read_mat(
            str(file_path),
            variable_names=["TS"],
            ignore_fields=["Events", "nTrial", "FileName", "Trial", "Sync", "Header"],
        )
        trial_structure = data_simple["TS"]
        experiment_information = trial_structure["Expt"]
        datetime_string = experiment_information["ThorImageExperiment"]["Date"]["Attributes"]["date"]
        session_start_time = parser.parse(datetime_string)
        session_start_time = session_start_time.replace(tzinfo=ZoneInfo("America/Chicago"))

        metadata["NWBFile"].update(session_start_time=session_start_time)

        return metadata
