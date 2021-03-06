from pathlib import Path
from test.utils import TestUtils
from typing import Union

import pytest

from src.biota_models.coral.model.coral_constants import CoralConstants
from src.biota_models.coral.simulation.coral_transect_simulation import (
    CoralTransectSimulation,
)
from src.core.simulation.base_simulation import BaseSimulation


class TestCoralTransectSimulation:
    def test_coral_transect_simulation_ctor(self):
        test_sim = CoralTransectSimulation()
        assert issubclass(type(test_sim), BaseSimulation)
        assert test_sim.mode == "Transect"
