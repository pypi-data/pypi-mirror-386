from __future__ import annotations

import logging
import os
import xml.etree.ElementTree as ET
from importlib import metadata
from pathlib import Path
from typing import Dict, List, Union

import pydantic
from aind_behavior_services import (
    AindBehaviorRigModel,
)
from aind_behavior_services.rig.cameras import CameraController, CameraTypes
from aind_behavior_services.utils import get_fields_of_type

logger = logging.getLogger(__name__)


def get_cameras(
    rig_instance: AindBehaviorRigModel, exclude_without_video_writer: bool = True
) -> Dict[str, CameraTypes]:
    """
    Retrieves cameras from a rig instance.

    Extracts camera information from camera controllers within the rig model,
    optionally filtering based on video writer availability.

    Args:
        rig_instance: The rig model instance containing camera controllers
        exclude_without_video_writer: If True, exclude cameras without a video writer

    Returns:
        A dictionary mapping camera names to their types
    """
    cameras: dict[str, CameraTypes] = {}
    camera_controllers = [x[1] for x in get_fields_of_type(rig_instance, CameraController)]

    for controller in camera_controllers:
        if exclude_without_video_writer:
            these_cameras = {k: v for k, v in controller.cameras.items() if v.video_writer is not None}
        else:
            these_cameras = controller.cameras
        cameras.update(these_cameras)
    return cameras


ISearchable = Union[pydantic.BaseModel, Dict, List]


def snapshot_python_environment() -> Dict[str, str]:
    """
    Captures a snapshot of the current Python environment.

    Creates a record of all currently installed Python packages and their versions,
    useful for reproducibility and debugging purposes.

    Returns:
        A dictionary of package names and their versions
    """
    return {dist.name: dist.version for dist in metadata.distributions()}


def snapshot_bonsai_environment(
    config_file: os.PathLike = Path("./bonsai/bonsai.config"),
) -> Dict[str, str]:
    """
    Captures a snapshot of the Bonsai environment from a configuration file.

    Parses the Bonsai configuration file to extract information about installed
    packages and their versions.

    Args:
        config_file: Path to the Bonsai configuration file

    Returns:
        A dictionary of package IDs and their versions
    """
    tree = ET.parse(Path(config_file))
    root = tree.getroot()
    packages = root.findall("Packages/Package")
    return {leaf.attrib["id"]: leaf.attrib["version"] for leaf in packages}
