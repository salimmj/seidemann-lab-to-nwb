"""Primary script to run to convert an entire session of data using the NWBConverter."""
from nwb_conversion_tools.utils import load_dict_from_file, dict_deep_update

from seidemann_lab_to_nwb.2022embargo01 import 2022Embargo01NWBConverter
from pathlib import Path

example_path = Path("D:/ExampleNWBConversion")
example_session_id = example_path.stem
nwbfile_path = example_path / f"{example_session_id}.nwb"

metadata_path = Path(__file__) / "2022embargo01_metadata.yaml"
metadata_from_yaml = load_dict_from_file(metadata_path)

source_data = dict(
    Recording=dict(),
    LFP=dict(),
    Sorting=dict(),
    Behavior=dict(),
)

converter = 2022Embargo01NWBConverter(source_data=source_data)

metadata = converter.get_metadata()
metadata = dict_deep_update(metadata, metadata_from_yaml)

converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path)