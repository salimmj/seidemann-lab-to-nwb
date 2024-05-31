"""Primary script to run to convert an entire session of data using the NWBConverter."""
from pathlib import Path
from datetime import datetime
from dateutil import tz

from neuroconv.utils import load_dict_from_file, dict_deep_update

from seidemann_lab_to_nwb.embargo22a import Embargo22ANWBConverter
from conversion_parameters import rows, columns, num_channels, rows_axis, columns_axis, num_channels_axis, frame_axis

data_path = Path("/home/heberto/seidemann/loki20210127/")
output_path = Path("/home/heberto/nwb/")
stub_test = True


if stub_test:
    output_path = output_path.parent / "nwb_stub"

session_id = data_path.stem


source_data = dict()
conversion_options = dict()

# Imaging
sampling_frequency = 30.0
dtype = "uint16"
file_path = data_path / "stream" / "Image_001_001.raw"
imaging_parameters = dict(
    file_path=str(file_path),
    num_rows=rows,
    num_columns=columns,
    num_channels=num_channels,
    rows_axis=rows_axis,
    columns_axis=columns_axis,
    channels_axis=num_channels_axis,
    frame_axis=frame_axis,
    sampling_frequency=sampling_frequency,
    dtype=dtype,
)
source_data.update(Imaging=imaging_parameters)
conversion_options.update(Imaging=dict(stub_test=stub_test))

# Suite2P
plane_no = 0
folder_path = data_path / "stream" / "suite2p"
source_data.update(Suit2P=dict(file_path=str(folder_path), plane_no=plane_no))

# Behavior
session_path = data_path / "stream"
source_data.update(Behavior=dict(session_path=str(session_path)))

converter = Embargo22ANWBConverter(source_data=source_data)

# Metadata
metadata = converter.get_metadata()
metadata_path = Path(__file__).parent / "embargo22a_metadata.yml"
metadata_from_yaml = load_dict_from_file(metadata_path)
metadata = dict_deep_update(metadata, metadata_from_yaml, append_list=False)

nwb_file_name = f"{session_id}.nwb"
nwbfile_path = output_path / nwb_file_name
converter.run_conversion(
    nwbfile_path=str(nwbfile_path),
    metadata=metadata,
    conversion_options=conversion_options,
    overwrite=True,
)
