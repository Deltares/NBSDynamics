from pathlib import Path

import numpy as np
from netCDF4 import Dataset
from pandas import DataFrame, Series

from src.core.coral_model import Coral
from src.core.utils import DataReshape


class Output:
    """Output files based on predefined output content."""

    _file_name_map = None
    _file_name_his = None
    _outdir = None

    _map_output = None
    _his_output = None

    _map_data = None
    _his_data = None

    _xy_stations = None
    _idx_stations = None

    def __init__(
        self,
        outdir: Path,
        xy_coordinates: np.ndarray,
        outpoint: np.ndarray,
        first_date: Series,
    ):
        """Generate output files of CoralModel simulation. Output files are formatted as NetCDF4-files.

        :param outdir: directory to write the output to
        :param xy_coordinates: (x,y)-coordinates
        :param outpoint: boolean indicating per (x,y) point if his output is desired
        :param first_date: first date of simulation

        :type outdir: str
        :type xy_coordinates: numpy.ndarray
        :type outpoint: numpy.ndarray
        :type first_date: pandas
        """
        self.xy_coordinates = xy_coordinates
        self.outpoint = outpoint
        self.nout_his = len(xy_coordinates[outpoint, 0])
        self.set_xy_stations()
        self.space = len(xy_coordinates)

        self.first_date = first_date
        self.first_year = first_date.year

        self._outdir = outdir

    def __str__(self):
        """String-representation of Output."""
        return (
            f"Output exported:\n\t{self._map_output}\n\t{self._his_output}"
            if self.defined
            else f"Output undefined."
        )

    def __repr__(self):
        """Representation of Output."""
        return f"Output(xy_coordinates={self.xy_coordinates}, first_date={self.first_date})"

    @property
    def defined(self) -> bool:
        """Output is defined."""
        return False if self._map_output is None and self._his_output is None else True

    def define_output(
        self,
        output_type: str,
        lme: bool = True,
        fme: bool = True,
        tme: bool = True,
        pd: bool = True,
        ps: bool = True,
        calc: bool = True,
        md: bool = True,
    ):
        """Define output dictionary.

        :param output_type: mapping or history output
        :param lme: light micro-environment, defaults to True
        :param fme: flow micro-environment, defaults to True
        :param tme: thermal micro-environment, defaults to True
        :param pd: photosynthetic dependencies, defaults to True
        :param ps: population states, defaults to True
        :param calc: calcification rates, defaults to True
        :param md: morphological development, defaults to True

        :type output_type: str
        :type lme: bool, optional
        :type fme: bool, optional
        :type tme: bool, optional
        :type pd: bool, optional
        :type ps: bool, optional
        :type calc: bool, optional
        :type md: bool, optional
        """
        types = ("map", "his")
        if output_type not in types:
            msg = f"{output_type} not in {types}."
            raise ValueError(msg)

        setattr(self, f"_{output_type}_output", locals())

    @staticmethod
    def __file_ext(file_name: Path) -> Path:
        """Ensure NetCDF file extension.

        :param file_name: file name
        :type file_name: Path
        """
        if not isinstance(file_name, Path):
            file_name = Path(file_name)
        if file_name.suffix != ".nc":
            return f"{file_name.stem}.nc"
        return file_name

    @property
    def outdir(self) -> str:
        """
        :return: output directory
        :rtype: str
        """
        return self._outdir.stem

    @outdir.setter
    def set_outdir(self, output_folder: Path):
        """Output folder.

        :param output_folder: output folder for output files
        :type output_folder: None, str, list, tuple
        """
        if not isinstance(output_folder, Path):
            self._outdir = Path(output_folder)
            return
        self._outdir = output_folder

    @property
    def file_name_map(self) -> Path:
        """File name of mapping output.

        :rtype: str
        """
        if self._file_name_map is None:
            self._file_name_map = self.file_dir_map / "CoralModel_map.nc"

        return self._file_name_map

    @file_name_map.setter
    def file_name_map(self, file_name: Path):
        """
        :param file_name: file name of mapping output
        :type file_name: None, str
        """
        self._file_name_map = self.__file_ext(file_name)

    @property
    def file_dir_map(self) -> Path:
        """Full file directory of mapping output.

        :rtype: str
        """
        return self._outdir

    @property
    def file_name_his(self) -> Path:
        """File name of history output.

        :rtype: str
        """
        if self._file_name_his is None:
            self._file_name_his = self.file_dir_his / "CoralModel_his.nc"

        return self._file_name_his

    @file_name_his.setter
    def file_name_his(self, file_name: Path):
        """
        :param file_name: file name of history output
        :type file_name: str
        """
        self._file_name_his = self.__file_ext(file_name)

    @property
    def file_dir_his(self) -> Path:
        """Full file directory of history output.

        :rtype: str
        """
        return self._outdir

    def initiate_map(self, coral: Coral):
        """Initiate mapping output file in which annual output covering the whole model domain is stored.

        :param coral: coral animal
        :type coral: Coral
        """
        # Open netcdf data and initialize needed variables.
        if self._map_output is not None and any(self._map_output.values()):
            self._map_data = Dataset(self.file_name_map, "w", format="NETCDF4")
            self._map_data.description = "Mapped simulation data of the CoralModel."

            # dimensions
            self._map_data.createDimension("time", None)
            self._map_data.createDimension("nmesh2d_face", self.space)

            # variables
            t = self._map_data.createVariable("time", int, ("time",))
            t.long_name = "year"
            t.units = "years since 0 B.C."

            x = self._map_data.createVariable("nmesh2d_x", "f8", ("nmesh2d_face",))
            x.long_name = "x-coordinate"
            x.units = "m"

            y = self._map_data.createVariable("nmesh2d_y", "f8", ("nmesh2d_face",))
            y.long_name = "y-coordinate"
            y.units = "m"

            t[:] = self.first_year
            x[:] = self.xy_coordinates[:, 0]
            y[:] = self.xy_coordinates[:, 1]

            # initial conditions
            # Definition of methods to initialize the netcdf variables.
            def init_lme():
                light_set = self._map_data.createVariable(
                    "Iz", "f8", ("time", "nmesh2d_face")
                )
                light_set.long_name = "annual mean representative light-intensity"
                light_set.units = "micro-mol photons m-2 s-1"
                light_set[:, :] = 0

            def init_fme():
                flow_set = self._map_data.createVariable(
                    "ucm", "f8", ("time", "nmesh2d_face")
                )
                flow_set.long_name = "annual mean in-canopy flow"
                flow_set.units = "m s-1"
                flow_set[:, :] = 0

            def init_tme():
                temp_set = self._map_data.createVariable(
                    "Tc", "f8", ("time", "nmesh2d_face")
                )
                temp_set.long_name = "annual mean coral temperature"
                temp_set.units = "K"
                temp_set[:, :] = 0

                low_temp_set = self._map_data.createVariable(
                    "Tlo", "f8", ("time", "nmesh2d_face")
                )
                low_temp_set.long_name = "annual mean lower thermal limit"
                low_temp_set.units = "K"
                low_temp_set[:, :] = 0

                high_temp_set = self._map_data.createVariable(
                    "Thi", "f8", ("time", "nmesh2d_face")
                )
                high_temp_set.long_name = "annual mean upper thermal limit"
                high_temp_set.units = "K"
                high_temp_set[:, :] = 0

            def init_pd():
                pd_set = self._map_data.createVariable(
                    "PD", "f8", ("time", "nmesh2d_face")
                )
                pd_set.long_name = "annual sum photosynthetic rate"
                pd_set.units = "-"
                pd_set[:, :] = 0

            def init_ps():
                pt_set = self._map_data.createVariable(
                    "PT", "f8", ("time", "nmesh2d_face")
                )
                pt_set.long_name = (
                    "total living coral population at the end of the year"
                )
                pt_set.units = "-"
                pt_set[:, :] = coral.living_cover

                ph_set = self._map_data.createVariable(
                    "PH", "f8", ("time", "nmesh2d_face")
                )
                ph_set.long_name = "healthy coral population at the end of the year"
                ph_set.units = "-"
                ph_set[:, :] = coral.living_cover

                pr_set = self._map_data.createVariable(
                    "PR", "f8", ("time", "nmesh2d_face")
                )
                pr_set.long_name = "recovering coral population at the end of the year"
                pr_set.units = "-"
                pr_set[:, :] = 0

                pp_set = self._map_data.createVariable(
                    "PP", "f8", ("time", "nmesh2d_face")
                )
                pp_set.long_name = "pale coral population at the end of the year"
                pp_set.units = "-"
                pp_set[:, :] = 0

                pb_set = self._map_data.createVariable(
                    "PB", "f8", ("time", "nmesh2d_face")
                )
                pb_set.long_name = "bleached coral population at the end of the year"
                pb_set.units = "-"
                pb_set[:, :] = 0

            def init_calc():
                calc_set = self._map_data.createVariable(
                    "calc", "f8", ("time", "nmesh2d_face")
                )
                calc_set.long_name = "annual sum calcification rate"
                calc_set.units = "kg m-2 yr-1"
                calc_set[:, :] = 0

            def init_md():
                dc_set = self._map_data.createVariable(
                    "dc", "f8", ("time", "nmesh2d_face")
                )
                dc_set.long_name = "coral plate diameter"
                dc_set.units = "m"
                dc_set[0, :] = coral.dc

                hc_set = self._map_data.createVariable(
                    "hc", "f8", ("time", "nmesh2d_face")
                )
                hc_set.long_name = "coral height"
                hc_set.units = "m"
                hc_set[0, :] = coral.hc

                bc_set = self._map_data.createVariable(
                    "bc", "f8", ("time", "nmesh2d_face")
                )
                bc_set.long_name = "coral base diameter"
                bc_set.units = "m"
                bc_set[0, :] = coral.bc

                tc_set = self._map_data.createVariable(
                    "tc", "f8", ("time", "nmesh2d_face")
                )
                tc_set.long_name = "coral plate thickness"
                tc_set.units = "m"
                tc_set[0, :] = coral.tc

                ac_set = self._map_data.createVariable(
                    "ac", "f8", ("time", "nmesh2d_face")
                )
                ac_set.long_name = "coral axial distance"
                ac_set.units = "m"
                ac_set[0, :] = coral.ac

                vc_set = self._map_data.createVariable(
                    "Vc", "f8", ("time", "nmesh2d_face")
                )
                vc_set.long_name = "coral volume"
                vc_set.units = "m3"
                vc_set[0, :] = coral.volume

            conditions_funct = dict(
                lme=init_lme,
                fme=init_fme,
                tme=init_tme,
                pd=init_pd,
                ps=init_ps,
                calc=init_calc,
                md=init_md,
            )
            for key, v_func in conditions_funct.items():
                if self._map_output[key]:
                    v_func()

            self._map_data.close()

    def update_map(self, coral: Coral, year: int):
        """Write data as annual output covering the whole model domain.

        :param coral: coral animal
        :param year: simulation year

        :type coral: Coral
        :type year: int
        """
        if self._map_output is not None and any(self._map_output.values()):
            self._map_data = Dataset(self.file_name_map, mode="a")

            i = int(year - self.first_year)
            self._map_data["time"][i] = year

            def update_lme():
                self._map_data["Iz"][-1, :] = coral.light[:, -1]

            def update_fme():
                self._map_data["ucm"][-1, :] = coral.ucm

            def update_tme():
                self._map_data["Tc"][-1, :] = coral.temp[:, -1]
                self._map_data["Tlo"][-1, :] = (
                    coral.Tlo
                    if len(DataReshape.variable2array(coral.Tlo)) > 1
                    else coral.Tlo * np.ones(self.space)
                )
                self._map_data["Thi"][-1, :] = (
                    coral.Thi
                    if len(DataReshape.variable2array(coral.Thi)) > 1
                    else coral.Thi * np.ones(self.space)
                )

            def update_pd():
                self._map_data["PD"][-1, :] = coral.photo_rate.mean(axis=1)

            def update_ps():
                self._map_data["PT"][-1, :] = coral.pop_states[:, -1, :].sum(axis=1)
                self._map_data["PH"][-1, :] = coral.pop_states[:, -1, 0]
                self._map_data["PR"][-1, :] = coral.pop_states[:, -1, 1]
                self._map_data["PP"][-1, :] = coral.pop_states[:, -1, 2]
                self._map_data["PB"][-1, :] = coral.pop_states[:, -1, 3]

            def update_calc():
                self._map_data["calc"][-1, :] = coral.calc.sum(axis=1)

            def update_md():
                self._map_data["dc"][-1, :] = coral.dc
                self._map_data["hc"][-1, :] = coral.hc
                self._map_data["bc"][-1, :] = coral.bc
                self._map_data["tc"][-1, :] = coral.tc
                self._map_data["ac"][-1, :] = coral.ac
                self._map_data["Vc"][-1, :] = coral.volume

            conditions_funct = dict(
                lme=update_lme,
                fme=update_fme,
                tme=update_tme,
                pd=update_pd,
                ps=update_ps,
                calc=update_calc,
                md=update_md,
            )
            for key, v_func in conditions_funct.items():
                if self._map_output[key]:
                    v_func()

            self._map_data.close()

    @property
    def xy_stations(self) -> np.ndarray:
        """(x,y)-coordinates of the stations.

        :rtype: numpy.ndarray
        """
        return self._xy_stations

    def set_xy_stations(self):
        """Determine space indices based on the (x,y)-coordinates of the stations."""
        if self.xy_stations is None:
            x = self.xy_coordinates[:, 0]
            y = self.xy_coordinates[:, 1]

            x_station = self.xy_coordinates[self.outpoint, 0]
            y_station = self.xy_coordinates[self.outpoint, 1]

            idx = np.zeros(self.nout_his)

            for s in range(len(idx)):
                idx[s] = np.argmin((x - x_station[s]) ** 2 + (y - y_station[s]) ** 2)

            self._idx_stations = idx.astype(int)
            self._xy_stations = self.xy_coordinates[self._idx_stations, :]

    @property
    def idx_stations(self) -> np.ndarray:
        """Space indices of stations.

        :rtype: numpy.ndarray
        """
        return self._idx_stations

    def initiate_his(self):
        """Initiate history output file in which daily output at predefined locations within the model is stored."""
        if self._his_output is not None and any(self._his_output.values()):
            self._his_data = Dataset(self.file_name_his, "w", format="NETCDF4")
            self._his_data.description = "Historic simulation data of the CoralModel"

            # dimensions
            self._his_data.createDimension("time", None)
            self._his_data.createDimension("stations", len(self.xy_stations))

            # variables
            t = self._his_data.createVariable("time", "f8", ("time",))
            t.long_name = f"days since {self.first_date}"
            t.units = "days"

            x = self._his_data.createVariable(
                "station_x_coordinate", "f8", ("stations",)
            )
            y = self._his_data.createVariable(
                "station_y_coordinate", "f8", ("stations",)
            )

            # setup data set
            x[:] = self.xy_stations[:, 0]
            y[:] = self.xy_stations[:, 1]

            def init_lme():
                light_set = self._his_data.createVariable(
                    "Iz", "f8", ("time", "stations")
                )
                light_set.long_name = "representative light-intensity"
                light_set.units = "micro-mol photons m-2 s-1"

            def init_fme():
                flow_set = self._his_data.createVariable(
                    "ucm", "f8", ("time", "stations")
                )
                flow_set.long_name = "in-canopy flow"
                flow_set.units = "m s-1"

            def init_tme():
                temp_set = self._his_data.createVariable(
                    "Tc", "f8", ("time", "stations")
                )
                temp_set.long_name = "coral temperature"
                temp_set.units = "K"

                low_temp_set = self._his_data.createVariable(
                    "Tlo", "f8", ("time", "stations")
                )
                low_temp_set.long_name = "lower thermal limit"
                low_temp_set.units = "K"

                high_temp_set = self._his_data.createVariable(
                    "Thi", "f8", ("time", "stations")
                )
                high_temp_set.long_name = "upper thermal limit"
                high_temp_set.units = "K"

            def init_pd():
                pd_set = self._his_data.createVariable("PD", "f8", ("time", "stations"))
                pd_set.long_name = "photosynthetic rate"
                pd_set.units = "-"

            def init_ps():
                pt_set = self._his_data.createVariable("PT", "f8", ("time", "stations"))
                pt_set.long_name = "total coral population"
                pt_set.units = "-"

                ph_set = self._his_data.createVariable("PH", "f8", ("time", "stations"))
                ph_set.long_name = "healthy coral population"
                ph_set.units = "-"

                pr_set = self._his_data.createVariable("PR", "f8", ("time", "stations"))
                pr_set.long_name = "recovering coral population"
                pr_set.units = "-"

                pp_set = self._his_data.createVariable("PP", "f8", ("time", "stations"))
                pp_set.long_name = "pale coral population"
                pp_set.units = "-"

                pb_set = self._his_data.createVariable("PB", "f8", ("time", "stations"))
                pb_set.long_name = "bleached coral population"
                pb_set.units = "-"

            def init_calc():
                calc_set = self._his_data.createVariable(
                    "G", "f8", ("time", "stations")
                )
                calc_set.long_name = "calcification"
                calc_set.units = "kg m-2 d-1"

            def init_md():
                dc_set = self._his_data.createVariable("dc", "f8", ("time", "stations"))
                dc_set.long_name = "coral plate diameter"
                dc_set.units = "m"

                hc_set = self._his_data.createVariable("hc", "f8", ("time", "stations"))
                hc_set.long_name = "coral height"
                hc_set.units = "m"

                bc_set = self._his_data.createVariable("bc", "f8", ("time", "stations"))
                bc_set.long_name = "coral base diameter"
                bc_set.units = "m"

                tc_set = self._his_data.createVariable("tc", "f8", ("time", "stations"))
                tc_set.long_name = "coral plate thickness"
                tc_set.units = "m"

                ac_set = self._his_data.createVariable("ac", "f8", ("time", "stations"))
                ac_set.long_name = "coral axial distance"
                ac_set.units = "m"

                vc_set = self._his_data.createVariable("Vc", "f8", ("time", "stations"))
                vc_set.long_name = "coral volume"
                vc_set.units = "m3"

            # initial conditions
            conditions_funct = dict(
                lme=init_lme,
                fme=init_fme,
                tme=init_tme,
                pd=init_pd,
                ps=init_ps,
                calc=init_calc,
                md=init_md,
            )
            for key, v_func in conditions_funct.items():
                if self._his_output[key]:
                    v_func()
            self._his_data.close()

    def update_his(self, coral: Coral, dates: DataFrame):
        """Write data as daily output at predefined locations within the model domain.

        :param coral: coral animal
        :param dates: dates of simulation year

        :type coral: Coral
        :type dates: DataFrame
        """
        if self._his_output is not None and any(self._his_output.values()):
            self._his_data = Dataset(self.file_name_his, mode="a")
            y_dates = dates.reset_index(drop=True)
            ti = (y_dates - self.first_date).dt.days.values
            self._his_data["time"][ti] = y_dates.values

            def update_lme():
                self._his_data["Iz"][ti, :] = coral.light[
                    self.idx_stations, :
                ].transpose()

            def update_fme():
                self._his_data["ucm"][ti, :] = np.tile(coral.ucm, (len(y_dates), 1))[
                    :, self.idx_stations
                ]

            def update_tme():
                self._his_data["Tc"][ti, :] = coral.temp[
                    self.idx_stations, :
                ].transpose()
                if (
                    len(DataReshape.variable2array(coral.Tlo)) > 1
                    and len(DataReshape.variable2array(coral.Thi)) > 1
                ):
                    self._his_data["Tlo"][ti, :] = np.tile(
                        coral.Tlo, (len(y_dates), 1)
                    )[:, self.idx_stations]
                    self._his_data["Thi"][ti, :] = np.tile(
                        coral.Thi, (len(y_dates), 1)
                    )[:, self.idx_stations]
                else:
                    self._his_data["Tlo"][ti, :] = coral.Tlo * np.ones(
                        (len(y_dates), len(self.idx_stations))
                    )
                    self._his_data["Thi"][ti, :] = coral.Thi * np.ones(
                        (len(y_dates), len(self.idx_stations))
                    )

            def update_pd():
                self._his_data["PD"][ti, :] = coral.photo_rate[
                    self.idx_stations, :
                ].transpose()

            def update_ps():
                self._his_data["PT"][ti, :] = (
                    coral.pop_states[self.idx_stations, :, :].sum(axis=2).transpose()
                )
                self._his_data["PH"][ti, :] = coral.pop_states[
                    self.idx_stations, :, 0
                ].transpose()
                self._his_data["PR"][ti, :] = coral.pop_states[
                    self.idx_stations, :, 1
                ].transpose()
                self._his_data["PP"][ti, :] = coral.pop_states[
                    self.idx_stations, :, 2
                ].transpose()
                self._his_data["PB"][ti, :] = coral.pop_states[
                    self.idx_stations, :, 3
                ].transpose()

            def update_calc():
                self._his_data["G"][ti, :] = coral.calc[
                    self.idx_stations, :
                ].transpose()

            def update_md():
                self._his_data["dc"][ti, :] = np.tile(coral.dc, (len(y_dates), 1))[
                    :, self.idx_stations
                ]
                self._his_data["hc"][ti, :] = np.tile(coral.hc, (len(y_dates), 1))[
                    :, self.idx_stations
                ]
                self._his_data["bc"][ti, :] = np.tile(coral.bc, (len(y_dates), 1))[
                    :, self.idx_stations
                ]
                self._his_data["tc"][ti, :] = np.tile(coral.tc, (len(y_dates), 1))[
                    :, self.idx_stations
                ]
                self._his_data["ac"][ti, :] = np.tile(coral.ac, (len(y_dates), 1))[
                    :, self.idx_stations
                ]
                self._his_data["Vc"][ti, :] = np.tile(coral.volume, (len(y_dates), 1))[
                    :, self.idx_stations
                ]

            conditions_funct = dict(
                lme=update_lme,
                fme=update_fme,
                tme=update_tme,
                pd=update_pd,
                ps=update_ps,
                calc=update_calc,
                md=update_md,
            )
            for key, v_func in conditions_funct.items():
                if self._his_output[key]:
                    v_func()

            self._his_data.close()