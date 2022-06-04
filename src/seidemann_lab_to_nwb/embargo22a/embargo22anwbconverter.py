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

        file_path = self.session_path / "M22D20210127R0Data2P20201001.mat"
        data_simple = read_mat(
            str(file_path), variable_names=["TS"], ignore_fields=["Events", "nTrial", "FileName", "Sync", "Header"]
        )
        trial_structure = data_simple["TS"]

        # Trial data
        trial_data = trial_structure["Trial"]
        df_trial_data = pd.DataFrame(trial_data)

        df_valid_trials = df_trial_data.query("FlagOIBLK == 1")  # Flag for imaging extraction
        trial_start_times = df_valid_trials["TimeOITrigger"]

        frames_per_trial = 75
        sampling_frequency = 30.0
        sampling_period = 1.0 / sampling_frequency

        timestamps = []
        for start_time in trial_start_times:
            start = start_time
            stop = sampling_period * frames_per_trial + start_time
            timestamps.append(np.linspace(start=start, stop=stop, num=frames_per_trial))

        timestamps = np.concatenate(timestamps)
        imaging_interface = self.data_interface_objects["Imaging"]
        imaging_extractor = imaging_interface.imaging_extractor
        imaging_extractor.set_times(times=timestamps)

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
