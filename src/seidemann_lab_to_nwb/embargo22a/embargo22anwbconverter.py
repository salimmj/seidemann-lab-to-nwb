"""Primary NWBConverter class for this dataset."""
from pathlib import Path
from pymatreader import read_mat
from dateutil import parser
from zoneinfo import ZoneInfo


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

    def get_metadata(self):
        metadata = super().get_metadata()

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
