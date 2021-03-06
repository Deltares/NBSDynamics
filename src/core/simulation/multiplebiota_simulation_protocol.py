from typing import List, Protocol, runtime_checkable

from src.core.biota.biota_model import Biota
from src.core.common.base_constants import BaseConstants
from src.core.common.environment import Environment
from src.core.hydrodynamics.hydrodynamic_protocol import HydrodynamicProtocol
from src.core.simulation.biota_wrapper import BiotaWrapper


@runtime_checkable
class MultipleBiotaSimulationProtocol(Protocol):
    @property
    def mode(self) -> str:
        """
        Name of the mode the simulation should run.

        Raises:
            NotImplementedError: When the model does not implement its own definition.

        Returns:
            str: Hydrodynamic mode name.
        """
        raise NotImplementedError

    @property
    def hydrodynamics(self) -> HydrodynamicProtocol:
        """
        Instance of hydrodynamic model.

        Raises:
            NotImplementedError: When the model does not implement its own definition.

        Returns:
            HydrodynamicProtocol: Instantiated object.
        """
        raise NotImplementedError

    @property
    def environment(self) -> Environment:
        """
        Environment in which the simulation takes place.

        Raises:
            NotImplementedError: When the model does not implement its own definition.

        Returns:
            Environment: Instantiated environment.
        """
        raise NotImplementedError

    @property
    def constants(self) -> BaseConstants:
        """
        Constants being used for calculations during simulation.

        Raises:
            NotImplementedError: When the model does not implement its own definition.

        Returns:
            Constants: Instance of Constants.
        """

    @property
    def biota_wrapper_list(self) -> List[BiotaWrapper]:
        """
        List of `BiotaWrapper` model object containing a `Biota` and `BaseOutputWrapper` each.

        Raises:
            NotImplementedError: When the model does not implement its own definition.

        Returns:
            List[BiotaWrapper]: List of available `BiotaWrapper`.
        """
        raise NotImplementedError

    def initiate(self, x_range: tuple, y_range: tuple, value: float) -> Biota:
        """
        Initiates the simulation attributes with the given parameters.

        Args:
            x_range (tuple): Minimum and maximum x-coordinate.
            y_range (tuple): Minimum and maximum y-coordinate.
            value (float): Biota cover.

        Raises:
            NotImplementedError: When the model does not implement its own definition.

        Returns:
            Biota: Initiated Biota object.
        """
        raise NotImplementedError

    def run(self, duration: int):
        """
        Run the simulation with the initiated attributes.

        Args:
            duration (int): Simulation duration [yrs].

        Raises:
            NotImplementedError: When the model does not implement its own definition.
        """
        raise NotImplementedError

    def finalise(self):
        """
        Finalizes simulation

        Raises:
            NotImplementedError: When the model does not implement its own definition.
        """
        raise NotImplementedError
