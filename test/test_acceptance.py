from pathlib import Path
from test.utils import TestUtils
from typing import Callable

import numpy as np
import pytest
from netCDF4 import Dataset
from numpy import loadtxt, savetxt

from src.biota_models.coral.simulation.coral_delft3d_simulation import (
    CoralDimrSimulation,
    CoralFlowFmSimulation,
)
from src.biota_models.coral.simulation.coral_transect_simulation import (
    CoralTransectSimulation,
)
from src.biota_models.vegetation.model.veg_constants import VegetationConstants
from src.biota_models.vegetation.model.veg_model import Vegetation
from src.biota_models.vegetation.simulation.veg_delft3d_simulation import (
    VegFlowFmSimulation, VegDimrSimulation
)
from src.biota_models.vegetation.simulation.veg_delft3D_simulation_MultipleSpecies import (
    VegFlowFmSimulation_MultipleSpecies,
)
from src.biota_models.vegetation.simulation.veg_delft3D_simulation_3species import (
    VegFlowFmSimulation_3species,
)
from src.biota_models.vegetation.simulation.veg_simulation_MultipleSpecies import (
    VegetationBiotaWrapper,
)
from src.core.simulation.multiplebiota_simulation_protocol import (
    MultipleBiotaSimulationProtocol,
)
from src.biota_models.mangroves.model.mangrove_constants import MangroveConstants
from src.biota_models.mangroves.model.mangrove_model import Mangrove
from src.biota_models.mangroves.simulation.mangrove_delft3d_simulation import MangroveFlowFmSimulation


from src.tools.plot_output import OutputHis, OutputMap, plot_output


class TestAcceptance:

    constants_input_file = "coral_input.txt"
    light_input_file = "TS_PAR.txt"
    temp_input_file = "TS_SST.txt"
    only_local = pytest.mark.skipif(
        not (TestUtils.get_external_repo("DimrDllDependencies")).is_dir(),
        reason="Only to be run using the DimrDllDependencies external repo.",
    )
    transect_local = pytest.mark.skipif(
        not (
            TestUtils.get_local_test_data_dir("transect_case")
            / "expected_output"
            / "nc_files"
        ).is_dir(),
        reason="Only to be run to generate expected data from local machines.",
    )

    @only_local
    def test_given_mangrove_case_runs(self):
        # test_dir = TestUtils.get_local_test_data_dir("delft3d_case")
        test_dir = TestUtils.get_local_test_data_dir("new_test")
        dll_repo = TestUtils.get_external_repo("DimrDllDependencies_23062020")
        kernels_dir = dll_repo / "kernels"

        assert test_dir.is_dir()
        assert kernels_dir.is_dir()

        test_case = test_dir / "input"
        sim_run = MangroveFlowFmSimulation(
            working_dir=test_dir,
            constants=MangroveConstants(),
            hydrodynamics=dict(
                working_dir=test_dir / "d3d_work",
                d3d_home=kernels_dir,
                dll_path=kernels_dir / "dflowfm_with_shared" / "bin" / "dflowfm",
                definition_file=test_case / "bdv9.mdu",
            ),
            output=dict(
                output_dir=test_dir / "output",
                map_output=dict(output_params=dict()),
                his_output=dict(
                    output_params=dict(),
                ),
            ),
            biota=Mangrove(constants=MangroveConstants()),
        )
        # Run simulation.
        # cover_path = test_case / "fm" / "cover"
        sim_run.initiate()  # add path to nc file of initial cover (map_file) if initial cover present
        sim_run.run(7)
        sim_run.finalise()

    @only_local
    def test_given_veg_case_runs(self):
        # test_dir = TestUtils.get_local_test_data_dir("delft3d_case")
        test_dir = TestUtils.get_local_test_data_dir("Zuidgors_bigger_ref")
        dll_repo = TestUtils.get_external_repo("DimrDllDependencies_23062020")
        kernels_dir = dll_repo / "kernels"

        assert test_dir.is_dir()
        assert kernels_dir.is_dir()

        test_case = test_dir / "input"
        species = "Spartina"
        veg_constants = VegetationConstants(species=species)
        sim_run = VegFlowFmSimulation(
            working_dir=test_dir,
            constants=veg_constants,
            hydrodynamics=dict(
                working_dir=test_dir / "d3d_work",
                d3d_home=kernels_dir,
                dll_path=kernels_dir / "dflowfm_with_shared" / "bin" / "dflowfm",
                definition_file=test_case / "Zuidgors_bigger_ref.mdu",
            ),
            output=dict(
                output_dir=test_dir / "output",
                map_output=dict(output_params=dict()),
                his_output=dict(
                    output_params=dict(),
                ),
            ),
            biota=Vegetation(species=species, constants=veg_constants),

        )

        # Run simulation.
        # cover_path = test_case / "fm" / "cover"
        sim_run.initiate()  # add path to nc file of initial cover (map_file) if initial cover present
        sim_run.run(2)
        sim_run.finalise()

        # 4. Verify expectations.
        # expected_dir = (
        #         TestUtils.get_local_test_data_dir("transect_case") / "expected_output"
        # )
        # compare_files(run_trans.output.his_output.output_filepath)
        # compare_files(run_trans.output.map_output.output_filepath)

        # 5. Verify plotting can be done.
        # plot_output(sim_run.output)

    @only_local
    def test_given_veg_case_runs_MultipleSpecies(self):
        # test_dir = TestUtils.get_local_test_data_dir("delft3d_case")
        test_dir = TestUtils.get_local_test_data_dir("Zuidgors_ref")
        dll_repo = TestUtils.get_external_repo("DimrDllDependencies_23062020")
        kernels_dir = dll_repo / "kernels"

        assert test_dir.is_dir()
        assert kernels_dir.is_dir()

        test_case = test_dir / "input"
        species1 = "Elytrigia"
        species2 = "Spartina"
        species3 = "Puccinellia"
        species4 = "Salicornia"
        veg_constants1 = VegetationConstants(species=species1)
        veg_constants2 = VegetationConstants(species=species2)
        veg_constants3 = VegetationConstants(species=species3)
        veg_constants4 = VegetationConstants(species=species4)

        sim_run = VegFlowFmSimulation_MultipleSpecies(
            working_dir=test_dir,
            constants=veg_constants1,
            hydrodynamics=dict(
                working_dir=test_dir / "d3d_work",
                d3d_home=kernels_dir,
                dll_path=kernels_dir / "dflowfm_with_shared" / "bin" / "dflowfm",
                definition_file=test_case / "Zuidgors_ref.mdu",
            ),
            biota_wrapper_list=[
                VegetationBiotaWrapper(
                    biota=Vegetation(species=species1, constants=veg_constants1),
                    output=dict(
                        output_dir=test_dir / "output",
                        map_output=dict(output_params=dict()),
                        his_output=dict(
                            output_params=dict(),
                        ),
                        species=species1,
                    ),
                ),
                VegetationBiotaWrapper(
                    biota=Vegetation(species=species2, constants=veg_constants2),
                    output=dict(
                        output_dir=test_dir / "output",
                        map_output=dict(output_params=dict()),
                        his_output=dict(
                            output_params=dict(),
                        ),
                        species=species2,
                    ),
                ),
                VegetationBiotaWrapper(
                    biota=Vegetation(species=species3, constants=veg_constants3),
                    output=dict(
                        output_dir=test_dir / "output",
                        map_output=dict(output_params=dict()),
                        his_output=dict(
                            output_params=dict(),
                        ),
                        species=species3,
                    ),
                ),
                VegetationBiotaWrapper(
                    biota=Vegetation(species=species4, constants=veg_constants4),
                    output=dict(
                        output_dir=test_dir / "output",
                        map_output=dict(output_params=dict()),
                        his_output=dict(
                            output_params=dict(),
                        ),
                        species=species4,
                    ),
                ),
            ],
            #morfac=100 #Optional input
        )

        # Run simulation.
        # cover_path = test_case / "fm" / "cover"
        sim_run.initiate()
        sim_run.run(1)
        sim_run.finalise()

    @only_local
    def test_given_veg_case_runs_3species(self):
        # test_dir = TestUtils.get_local_test_data_dir("delft3d_case")
        test_dir = TestUtils.get_local_test_data_dir("Zuidgors_ref")
        dll_repo = TestUtils.get_external_repo("DimrDllDependencies_23062020")
        kernels_dir = dll_repo / "kernels"

        assert test_dir.is_dir()
        assert kernels_dir.is_dir()

        test_case = test_dir / "input"
        species1 = "Elytrigia"
        species2 = "Spartina"
        species3 = "Puccinellia"
        veg_constants1 = VegetationConstants(species=species1)
        veg_constants2 = VegetationConstants(species=species2)
        veg_constants3 = VegetationConstants(species=species3)

        sim_run = VegFlowFmSimulation_3species(
            working_dir=test_dir,
            constants=veg_constants1,
            hydrodynamics=dict(
                working_dir=test_dir / "d3d_work",
                d3d_home=kernels_dir,
                dll_path=kernels_dir / "dflowfm_with_shared" / "bin" / "dflowfm",
                definition_file=test_case / "Zuidgors_ref.mdu",
            ),
            biota_wrapper_list=[
                VegetationBiotaWrapper(
                    biota=Vegetation(species=species1, constants=veg_constants1),
                    output=dict(
                        output_dir=test_dir / "output",
                        map_output=dict(output_params=dict()),
                        his_output=dict(
                            output_params=dict(),
                        ),
                        species=species1,
                    ),
                ),
                VegetationBiotaWrapper(
                    biota=Vegetation(species=species2, constants=veg_constants2),
                    output=dict(
                        output_dir=test_dir / "output",
                        map_output=dict(output_params=dict()),
                        his_output=dict(
                            output_params=dict(),
                        ),
                    ),
                ),
                VegetationBiotaWrapper(
                    biota=Vegetation(species=species3, constants=veg_constants3),
                    output=dict(
                        output_dir=test_dir / "output",
                        map_output=dict(output_params=dict()),
                        his_output=dict(
                            output_params=dict(),
                        ),
                    ),
                ),
            ],

        )

        # Run simulation.
        # cover_path = test_case / "fm" / "cover"
        sim_run.initiate()
        sim_run.run(20)
        sim_run.finalise()

    def test_given_transect_case_runs(self):
        # 1. Define test data.
        test_dir = TestUtils.get_local_test_data_dir("transect_case")
        assert test_dir.is_dir()

        # 1.b. Remove all output data in case it exists from previous runs.
        his_filename = "CoralModel_his.nc"
        map_filename = "CoralModel_map.nc"
        output_dir = test_dir / "output"

        his_output_file = output_dir / his_filename
        his_output_file.unlink(missing_ok=True)

        map_output_file = output_dir / map_filename
        map_output_file.unlink(missing_ok=True)

        # 2. Prepare model.
        # Define the basic Simulation object, indicating already here the type of hydrodynamics
        input_dir = test_dir / "input"
        run_trans = CoralTransectSimulation(
            working_dir=test_dir,
            constants=input_dir / self.constants_input_file,
            environment=dict(
                light=input_dir / self.light_input_file,
                temperature=input_dir / self.temp_input_file,
                storm=input_dir / "TS_stormcat2.txt",
                dates=("2000-01-01", "2100-01-01"),
            ),
            hydrodynamics=dict(
                definition_file=input_dir / "TS_waves.txt",
                config_file=input_dir / "config.csv",
            ),
            output=dict(
                output_dir=test_dir / "output",
                map_output=dict(output_params=dict(fme=False)),
                his_output=dict(output_params=dict(fme=False)),
            ),
            biota=dict(
                dc=0.125,
                hc=0.125,
                bc=0.1,
                tc=0.1,
                ac=0.2,
                Csp=0.6,
            ),
        )

        # 3. Run simulation
        run_trans.initiate()
        run_trans.run()
        run_trans.finalise()

        # 4. Verify expectations.
        expected_dir = (
            TestUtils.get_local_test_data_dir("transect_case") / "expected_output"
        )

        def compare_files(created_file: Path):
            def normalize_name_with_capitals(name: str) -> str:
                if any(x.isupper() for x in name):
                    return name + name
                return name

            ref_dir = expected_dir / created_file.stem.split("_")[-1]
            with Dataset(created_file, "r", format="NETCDF4") as out_netcdf:
                for variable in out_netcdf.variables:
                    variable_filename = normalize_name_with_capitals(variable)
                    expected_file = (
                        ref_dir / f"ref_{variable_filename}_{created_file.stem}.txt"
                    )
                    assert (
                        expected_file.is_file()
                    ), f"Expected file for variable {variable} not found at {expected_file}"
                    ref_variable = loadtxt(expected_file)
                    assert np.allclose(
                        ref_variable, out_netcdf[variable]
                    ), f"{variable} not close to reference data."

        compare_files(run_trans.output.his_output.output_filepath)
        compare_files(run_trans.output.map_output.output_filepath)

        # 5. Verify plotting can be done.
        plot_output(run_trans.output)

    # TODO: Delft3D dlls not yet available at the repo level.
    @only_local
    def test_given_delft3d_flowfm_case_runs(self):
        # Test based on interface_D3D.py
        test_dir = TestUtils.get_local_test_data_dir("delft3d_case")
        dll_repo = TestUtils.get_external_repo("DimrDllDependencies")
        assert test_dir.is_dir()
        kernels_dir = dll_repo / "kernels"
        test_case = dll_repo / "test_cases" / "c01_test1_smalltidalbasin_vegblock"

        input_dir = test_dir / "input"
        sim_run = CoralFlowFmSimulation(
            working_dir=test_dir,
            constants=input_dir / self.constants_input_file,
            environment=dict(
                light=input_dir / self.light_input_file,
                temperature=input_dir / self.temp_input_file,
            ),
            biota=dict(
                dc=0.1,
                hc=0.1,
                bc=0.05,
                tc=0.05,
                ac=0.2,
                species_constant=1,
            ),
            hydrodynamics=dict(
                working_dir=test_dir / "d3d_work",
                d3d_home=kernels_dir,
                dll_path=kernels_dir / "dflowfm_with_shared" / "bin" / "dflowfm.dll",
                definition_file=test_case / "fm" / "shallow_wave.mdu",
                update_interval=300,
                update_interval_storm=300,
            ),
            output=dict(
                output_dir=test_dir / "output",
                map_output=dict(output_params=dict(fme=False)),
                his_output=dict(
                    xy_stations=np.array([[0, 0], [1, 1]]),
                    output_params=dict(fme=False),
                ),
            ),
        )

        # Run simulation.
        sim_run.initiate()
        sim_run.run()
        sim_run.finalise()

    # TODO: Delft3D dlls not yet available at the repo level.
    @only_local
    def test_given_delft3d_dimr_case_runs(self):
        # Test based on interface_D3D.py
        test_dir = TestUtils.get_local_test_data_dir("delft3d_case")
        dll_repo = TestUtils.get_external_repo("DimrDllDependencies")
        assert test_dir.is_dir()
        kernels_dir = dll_repo / "kernels"
        test_case = dll_repo / "test_cases" / "c01_test1_smalltidalbasin_vegblock"

        input_dir = test_dir / "input"
        sim_run = CoralDimrSimulation(
            working_dir=test_dir,
            constants=input_dir / self.constants_input_file,
            environment=dict(
                light=input_dir / self.light_input_file,
                temperature=input_dir / self.temp_input_file,
            ),
            biota=dict(
                dc=0.1,
                hc=0.1,
                bc=0.05,
                tc=0.05,
                ac=0.2,
                species_constant=1,
            ),
            hydrodynamics=dict(
                working_dir=test_dir / "d3d_work",
                d3d_home=kernels_dir,
                dll_path=kernels_dir / "dimr_with_shared" / "bin" / "dimr_dll.dll",
                update_intervals=(300, 300),
                definition_file=test_case / "fm" / "shallow_wave.mdu",
                config_file=test_case / "dimr_config.xml",
            ),
            output=dict(
                output_dir=test_dir / "output",
                map_output=dict(output_params=dict(fme=False)),
                his_output=dict(
                    xy_stations=np.array([0, 0]), output_params=dict(fme=False)
                ),
            ),
        )

        # Run simulation.
        with pytest.raises(RuntimeError):
            # Delft3D dlls not yet available at the repo level.
            sim_run.initiate()
            sim_run.run()
            sim_run.finalise()

    @transect_local
    @pytest.mark.parametrize(
        "nc_filename",
        [
            pytest.param("CoralModel_his.nc", id="His variables"),
            pytest.param("CoralModel_map.nc", id="Map variables"),
        ],
    )
    def test_util_output_variables_netcdf(self, nc_filename: str):
        """
        This test is only meant to be run locally, it helps generating the expected data as .txt files.
        """
        expected_dir = (
            TestUtils.get_local_test_data_dir("transect_case") / "expected_output"
        )

        def normalize_name_with_capitals(name: str) -> str:
            if any(x.isupper() for x in name):
                return name + name
            return name

        def output_file(netcdf_file: Path):
            out_dir = netcdf_file.parent / netcdf_file.stem.split("_")[-1]
            out_dir.mkdir(parents=True, exist_ok=True)
            with Dataset(netcdf_file, "r", format="NETCDF4") as ref_netcdf:
                for variable in ref_netcdf.variables:
                    variable_name = normalize_name_with_capitals(variable)
                    ref_file = out_dir / f"ref_{variable_name}_{netcdf_file.stem}.txt"
                    savetxt(ref_file, ref_netcdf[variable])

        output_file(expected_dir / nc_filename)

    @transect_local
    @pytest.mark.parametrize(
        "nc_filename, output_type",
        [
            pytest.param("CoralModel_his.nc", OutputHis, id="Plot HIS local file."),
            pytest.param("CoralModel_map.nc", OutputMap, id="Plot MAP local file."),
        ],
    )
    def test_plot_output(self, nc_filename: str, output_type: Callable):
        expected_file = (
            TestUtils.get_local_test_data_dir("transect_case") / "output" / nc_filename
        )
        output_type().plot(expected_file)
