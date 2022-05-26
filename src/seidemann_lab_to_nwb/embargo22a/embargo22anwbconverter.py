"""Primary NWBConverter class for this dataset."""
from nwb_conversion_tools import (
    NWBConverter,
    Suite2pSegmentationInterface
)

from seidemann_lab_to_nwb.embargo22a import Embargo22ABehaviorInterface


class Embargo22ANWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        Suit2P=Suite2pSegmentationInterface,
        Behavior=Embargo22ABehaviorInterface,
    )
