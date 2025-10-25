import logging
from pathlib import Path

import numpy as np
import pandas as pd
from seabirdfilehandler import CnvFile

from processing.module import ArrayModule

logger = logging.getLogger(__name__)


class AirPressureCorrection(ArrayModule):
    """
    Corrects water pressure by the given air pressure.
    """

    def __call__(
        self,
        input: Path | str | CnvFile | pd.DataFrame | np.ndarray,
        parameters: dict = {},
        output: str = "cnvobject",
        output_name: str | None = None,
        **kwargs,
    ) -> None | CnvFile | pd.DataFrame | np.ndarray:
        return super().__call__(input, parameters, output, output_name)

    def transformation(self) -> bool:
        """
        Base logic to correct pressure.
        """
        try:
            prDM = self.cnv.parameters["prDM"].data
            air_pressure = float(
                self.cnv.metadata["Air_Pressure"].replace("hPa", "")
            )
        except KeyError:
            return False
        except ValueError:
            return False

        water_pressure = 1024
        pressure_diff = round((air_pressure - water_pressure) / 100, 4)
        self.cnv.parameters["prDM"].data = prDM - pressure_diff
        self.parameters["pressure_diff"] = str(pressure_diff)

        return True
