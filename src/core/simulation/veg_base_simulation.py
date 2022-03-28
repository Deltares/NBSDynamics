from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import pandas as pd
from pydantic import validator
from tqdm import tqdm
from datetime import timedelta

from src.core import RESHAPE
from src.core.base_model import BaseModel
from src.core.bio_process.veg_colonisation import Colonization
from src.core.bio_process.veg_mortality import Veg_Mortaility
from src.core.bio_process.veg_growth import Veg_Growth
from src.core.bio_process.veg_hydro_morphodynamics import Hydro_Morphodynamics
from src.core.common.constants_veg import Constants
from src.core.common.environment import Environment
from src.core.common.space_time import time_series_year
from src.core.vegetation.veg_model import Vegetation
from src.core.hydrodynamics.factory import HydrodynamicsFactory
from src.core.hydrodynamics.hydrodynamic_protocol import HydrodynamicProtocol
from src.core.output.output_wrapper import OutputWrapper


class BaseSimulation(BaseModel, ABC):
    """
    Implements the `SimulationProtocol`.
    Facade class that can be implemented through an Adapter pattern.
    VegetationModel simulation.
    """

    mode: str

    # Directories related to working dir
    working_dir: Optional[Path] = Path.cwd()
    figures_dir: Path = working_dir / "figures"
    output_dir: Path = working_dir / "output"
    input_dir: Path = working_dir / "input"

    # Other fields.
    hydrodynamics: Optional[HydrodynamicProtocol]
    environment: Environment = Environment()
    constants: Constants = Constants()
    output: Optional[VegOutputWrapper]
    veg: Optional[Vegetation]

    @validator("constants", pre=True)
    @classmethod
    def validate_constants(cls, field_value: Union[str, Path, Constants]) -> Constants:
        """
        Validates the user-input constants value and transforms in case it's a filepath (str, Path).

        Args:
            field_value (Union[str, Path, Constants]): Value given by the user representing Constants.

        Raises:
            NotImplementedError: When the input value does not have any converter.

        Returns:
            Constants: Validated constants value.
        """
        if isinstance(field_value, Constants):
            return field_value
        if isinstance(field_value, str):
            field_value = Path(field_value)
        if isinstance(field_value, Path):
            return Constants.from_input_file(field_value)
        raise NotImplementedError(f"Validator not available for {type(field_value)}")


    @validator("veg", pre=True)
    @classmethod
    def validate_veg(cls, field_value: Union[dict, Vegetation], values: dict) -> Vegetation:
        """
        Initializes vegetation in case a dictionary is provided. Ensuring the constants are also
        given to the object.

        Args:
            field_value (Union[dict, Vegetation]): Value given by the user for the Vegetation field.
            values (dict): Dictionary of remaining user-given field values.

        Returns:
            Vegetation: Validated instance of 'Vegetation'.
        """
        if isinstance(field_value, Vegetation):
            return field_value
        if isinstance(field_value, dict):
            # Check if constants present in the dictionary:
            if "constants" in field_value.keys():
                # It will be generated automatically.
                # in case parameters are missing an error will also be displayed.
                return Vegetation(**field_value)
            if "constants" in values.keys():
                field_value["constants"] = values["constants"]
                return Vegetation(**field_value)
            raise ValueError(
                "Constants should be provided to initialize a Vegetation Model."
            )
        raise NotImplementedError(f"Validator not available for {type(field_value)}")


    @validator("hydrodynamics", pre=True, always=True)
    @classmethod
    def validate_hydrodynamics_present(
            cls, field_values: Union[dict, HydrodynamicProtocol], values: dict
    ) -> HydrodynamicProtocol:
        """
        Validator to transform the given dictionary into the corresponding hydrodynamic model.

        Args:
            field_values (Union[dict, HydrodynamicProtocol]): Value assigned to `hydrodynamics`.
            values (dict): Dictionary of values given by the user.

        Raises:
            ValueError: When no hydrodynamics model can be built with the given values.

        Returns:
            dict: Validated dictionary of values given by the user.
        """
        if field_values is None:
            field_values = dict()
        if isinstance(field_values, dict):
            return HydrodynamicsFactory.create(
                field_values.get("mode", values["mode"]), **field_values
            )

        return field_values

    @abstractmethod
    def configure_hydrodynamics(self):
        """
        Configures the parameters for the `HydrodynamicsProtocol`.

        Raises:
            NotImplementedError: When abstract method not defined in concrete class.
        """
        raise NotImplementedError

    @abstractmethod
    def configure_output(self):
        """
        Configures the parameters for the `OutputWrapper`.
        """
        raise NotImplementedError

    def validate_simulation_directories(self):
        """
        Generates the required directories if they do not exist already.
        """
        loop_dirs: List[Path] = [
            "working_dir",
            "output_dir",
            "input_dir",
            "figures_dir",
        ]
        for loop_dir in loop_dirs:
            value_dir: Path = getattr(self, loop_dir)
            if not value_dir.is_dir():
                value_dir.mkdir(parents=True)


    def initiate(
        self,
        x_range: Optional[tuple] = None,
        y_range: Optional[tuple] = None,
        value: Optional[float] = None,
    ) -> Vegetation:
        """Initiate the vegetation distribution.
        The default vegetation distribution is no initial vegetation cover.

        :param x_range: minimum and maximum x-coordinate, defaults to None
        :param y_range: minimum and maximum y-coordinate, defaults to None
        :param value: coral cover, defaults to None

        :type veg: Vegetation
        :type x_range: tuple, optional
        :type y_range: tuple, optional
        :type value: float, optional

        :return: vegetation characteristics initiated
        :rtype: Vegetation
        """
        self.configure_hydrodynamics()
        self.configure_output()
        # Load constants and validate environment.
        self.validate_simulation_directories()

        RESHAPE().space = self.hydrodynamics.space

        if self.output.defined:
            self.output.initialize(self.veg)
        else:
            print("WARNING: No output defined, so none exported.")

        xy = self.hydrodynamics.xy_coordinates

        ##TODO define cover as a possible input variable!
        cover = np.ones(RESHAPE().space)

        if x_range is not None:
            x_min = x_range[0] if x_range[0] is not None else min(xy[:][0])
            x_max = x_range[1] if x_range[1] is not None else max(xy[:][0])
            cover[np.logical_or(xy[:][0] <= x_min, xy[:][0] >= x_max)] = 0

        if y_range is not None:
            y_min = y_range[0] if y_range[0] is not None else min(xy[:][1])
            y_max = y_range[1] if y_range[1] is not None else max(xy[:][1])
            cover[np.logical_or(xy[:][1] <= y_min, xy[:][1] >= y_max)] = 0

        self.veg.initiate_vegetation_characteristics(cover)

        ## TODO create new output model for vegetation!
        self.output.initialize(self.veg)

    def run(self, duration: Optional[int] = None):
        """Run simulation.

        :param veg: vegetation
        :param duration: simulation duration [yrs], defaults to None

        :type veg: Vegetation
        :type duration: int, optional
        """
        # auto-set duration based on constants value (provided or default)
        if duration is None:
            duration = int(
                self.constants.sim_duration
            )
        start_date =  pd.to_datetime(self.constants.start_date)
        years = range(
            int(start_date.year),
            int(start_date.year + duration),
        )   # takes the starting year from the start date defined in the Constants class.

        with tqdm(range((int(duration)))) as progress:
            for i in progress:
                current_year = years[i]
                for ets in self.constants.ets_per_year:

                    # # TODO: determine current time period it is in depending on year and ets within year
                    ets_duration = 365/ets # duration of each ets in days
                    if ets == 0:
                        begin_date = pd.Timestamp(year=current_year,  month=start_date.month, day=start_date.day)
                    else:
                        begin_date = end_date + timedelta(days=1)
                    end_date = begin_date + timedelta(days=ets_duration)


                    # # set dimensions (i.e. update time-dimension)
                    ## TODO Do I need this?
                    # RESHAPE().time = len(
                    #      environment_dates.dt.year[environment_dates.dt.year == years[i]]
                    #  )

                    # if-statement that encompasses all for which the hydrodynamic should be used
                    ## TODO update this with values actually needed
                    progress.set_postfix(inner_loop=f"update {self.hydrodynamics}")
                    bed_level, wave_vel, wave_per = self.hydrodynamics.update(
                        self.veg
                    )

                    # # environment
                    progress.set_postfix(inner_loop="vegetation environment")
                    # flow micro-environment
                    ## ToDO update this according to veg_hydro_morphodynamics
                    fme = Flow(
                        u_current=current_vel,
                        u_wave=wave_vel,
                        h=self.hydrodynamics.water_depth,
                        peak_period=wave_per,
                        constants=self.constants,
                    )
                    fme.velocities(self.coral, in_canopy=self.constants.fme)

                    # # vegetation dynamics
                    progress.set_postfix(inner_loop="vegetation dynamics")
                    # vegetation mortality (ALWAYS HAPPEN)
                    ## TODO update this when known what needed in mortality class!
                    mort = Veg_Mortaility(
                        constants=self.constants,
                    )
                    mort.update(self.veg)

                    # # vegetation growth (only when season right for growth)
                    if self.veg.growth_days[ets] > 0: #if there is growth days, do growth function
                        growth = Veg_Growth(constants=self.constants)
                        growth.update(self.veg, ets)

                    # # colonization (only in colonization period)
                    if self.veg.col_days[ets] > 0:
                        progress.set_postfix(inner_loop="vegetation colonization")
                        col = Colonization(constants=self.constants)
                        col.update(self.vegetation, )

                    # # export results
                    progress.set_postfix(inner_loop="export results")
                    ## TODO check this when finishing the output files!
                    # map-file
                    self.output.map_output.update(self.coral, years[i])
                    # his-file
                    self.output.his_output.update(
                        self.coral,
                        environment_dates[environment_dates.dt.year == years[i]],
                    )

    def finalise(self):
        """Finalise simulation."""
        ## TODO what does this do? Does is need modification?
        self.hydrodynamics.finalise()