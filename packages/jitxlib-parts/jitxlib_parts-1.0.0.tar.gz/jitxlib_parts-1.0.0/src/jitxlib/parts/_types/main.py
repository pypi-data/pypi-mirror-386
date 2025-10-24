import os
import logging

from ..commands import PartJSON, download_model3d
from .capacitor import Capacitor
from .component import Part, ComponentCode
from .resistor import Resistor
from .inductor import Inductor


logger = logging.getLogger(__name__)


def to_component(json: PartJSON) -> Part:
    return parse_component(json)


def parse_component(json: PartJSON) -> Part:
    if "category" not in json:
        logger.warning("Part data from database has no category.")
        return Part.from_dict(json)

    match json["category"]:
        case "resistor":
            return Resistor.from_dict(json)
        case "capacitor":
            return Capacitor.from_dict(json)
        case "inductor":
            return Inductor.from_dict(json)
        case _:
            return Part.from_dict(json)


def download_model3d_files(
    component_code: ComponentCode, parent_folder: str | None = None
) -> tuple[str, ...]:
    """
    Download model 3D files if they are not already downloaded.

    Case 1: parent_folder is None when the DB part is created on the fly.
    Download the model3d files to the filename in the Model3D statement..

    Case 2: Otherwise, parent_folder is the folder where the Landpattern class is located.
    Download to "parent_folder/jitx-01234.stp".
    """
    if component_code.landpattern is None:
        return ()

    failed_model3ds = []
    for model3d in component_code.landpattern.model3ds:
        if not isinstance(model3d.filename, str):
            continue
        if parent_folder is None:
            resolved_filename = os.path.abspath(model3d.filename)
        else:
            resolved_filename = os.path.abspath(
                os.path.join(parent_folder, model3d.filename)
            )
        if os.path.exists(resolved_filename):
            continue
        try:
            download_model3d(resolved_filename)
        except Exception:
            failed_model3ds.append(model3d.jitx_model_3d_id)

    return tuple(failed_model3ds)
