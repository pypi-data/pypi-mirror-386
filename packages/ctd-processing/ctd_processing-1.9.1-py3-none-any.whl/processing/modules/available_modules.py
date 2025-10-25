from pathlib import Path

import gsw

from processing.module import Module
from processing.modules.air_pressure_correction import AirPressureCorrection
from processing.modules.cast_borders import CastBorders
from processing.modules.create_bottlefile import create_bottle_file
from processing.modules.external_functions import (
    ExternalFunctionCaller,
    ExternalFunctions,
)
from processing.modules.geomar_wildedit import WildeditGEOMAR
from processing.modules.seabird_functions import AlignCTD
from processing.utils import default_seabird_exe_path

mapper = {
    "airpressure": AirPressureCorrection(),
    "alignctd": AlignCTD(),
    "cast_borders": CastBorders(),
    "create_bottle_file": create_bottle_file,
    "wildedit_geomar": WildeditGEOMAR(),
}

processing_functions = ExternalFunctions([gsw])


def map_proc_name_to_class(module: str) -> Module:
    """
    Sets and maps the known processing modules to their respective
    module classes.

    Parameters
    ----------
    module: str :
        Name of the module, that is being used inside the config.

    Returns
    -------

    """
    if module in processing_functions.list_of_function_names():
        return ExternalFunctionCaller(module, processing_functions)
    else:
        return mapper[module.lower()]


def get_list_of_custom_exes(
    path_to_custom_exe_dir: Path | str | None = None,
) -> list[str]:
    if isinstance(path_to_custom_exe_dir, Path | str):
        return [exe.stem for exe in Path(path_to_custom_exe_dir).glob("*.exe")]
    else:
        return []


def get_list_of_installed_seabird_modules() -> list[str]:
    seabird_path = default_seabird_exe_path()
    return [str(file.stem)[:-1] for file in seabird_path.glob("*W.exe")]


def get_dict_of_available_processing_modules(
    path_to_custom_exe_dir: Path | str | None = None,
) -> dict:
    proc_dict = {
        "custom": [
            *list(mapper.values()),
            *get_list_of_custom_exes(path_to_custom_exe_dir),
        ],
        "seabird_exes": get_list_of_installed_seabird_modules(),
        **processing_functions,
    }
    return proc_dict
