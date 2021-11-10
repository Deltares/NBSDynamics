"""
coral_mostoel - environment

@author: Gijs G. Hendrickx
@contributor: Peter M.J. Herman
"""

from datetime import datetime
from pathlib import Path
import numpy as np

import pandas as pd
from src.core.base_model import BaseModel
from typing import Optional, Union
from pydantic import validator

EnvInputAttr = Union[pd.DataFrame, Path]


class Environment(BaseModel):
    dates: Optional[pd.DataFrame]
    light: Optional[pd.DataFrame]
    light_attenuation: Optional[pd.DataFrame]
    temperature: Optional[pd.DataFrame]
    aragonite: Optional[pd.DataFrame]
    storm_category: Optional[pd.DataFrame]

    @validator("light", "light_attenuation", "temperature", "aragonite", pre=True)
    @classmethod
    def validate_dataframe_from_file(value: EnvInputAttr) -> pd.DataFrame:
        """
        Transforms an input into the expected type for the parameter. In case a file it's provided
        it's content is converted into a pandas DataFrame.

        Args:
            value (Union[pd.DataFrame, Path]): Value to be validated.

        Returns:
            pd.DataFrame: Validated attribute value.
        """

        def read_index(value_file: Path) -> pd.DataFrame:
            """Function applicable to time-series in Pandas."""
            time_series = pd.read_csv(value_file, sep="\t")
            if time_series.isnull().values.any():
                msg = f"NaNs detected in time series {value_file}"
                raise ValueError(msg)
            time_series["date"] = pd.to_datetime(time_series["date"])
            time_series.set_index("date", inplace=True)
            return time_series

        if isinstance(value, pd.DataFrame):
            return value
        if isinstance(value, Path):
            if not value.is_file():
                raise FileNotFoundError(value)
            return read_index(value)
        raise NotImplementedError(f"Validator not available for type {type(value)}")

    @validator("storm_category")
    @classmethod
    def validate_storm_category(value: EnvInputAttr) -> pd.DataFrame:
        if isinstance(value, pd.DataFrame):
            return value
        if isinstance(value, Path):
            if not value.is_file():
                raise FileNotFoundError(value)
            csv_values = pd.read_csv(value, sep="\t")
            csv_values.set_index("year", inplace=True)
            return csv_values
        raise NotImplementedError(f"Validator not available for type {type(value)}")

    def set_dates(
        self, start_date: Union[str, datetime], end_date: Union[str, datetime]
    ):
        """
        Set dates manually, ignoring possible dates in environmental time-series.

        Args:
            start_date (Union[str, datetime]): Start of the range dates.
            end_date (Union[str, datetime]): End of the range dates.
        """
        dates = pd.date_range(start_date, end_date, freq="D")
        self.dates = pd.DataFrame({"date": dates})

    EnvironmentValue = Union[float, list, tuple, np.ndarray, pd.DataFrame]

    def set_parameter_values(
        self, parameter: str, value: EnvironmentValue, pre_date: Optional[int] = None
    ):
        """
        Set the time-series data to a time-series, or a  value. In case :param value: is not iterable, the
        :param parameter: is assumed to be constant over time. In case :param value: is iterable, make sure its length
        complies with the simulation length.

        Included parameters:
            light                       :   incoming light-intensity [umol photons m-2 s-1]
            LAC / light_attenuation     :   light attenuation coefficient [m-1]
            temperature                 :   sea surface temperature [K]
            aragonite                   :   aragonite saturation state [-]
            storm                       :   storm category, annually [-]

        Args:
            parameter (str): Parameter to be set.
            value (EnvironmentValue): New value for the parameter.
            pre_date (Optional[int], optional): Time-series start before simulation dates [yrs]. Defaults to None.
        """

        def set_value(val):
            """Function to set  value."""
            if pre_date is None:
                return pd.DataFrame({parameter: val}, index=self.dates)

            dates = pd.date_range(
                self.dates.iloc[0] - pd.DateOffset(years=pre_date),
                self.dates.iloc[-1],
                freq="D",
            )
            return pd.DataFrame({parameter: val}, index=dates)

        if self.dates is None:
            msg = (
                f"No dates are defined. "
                f"Please, first specify the dates before setting the time-series of {parameter}; "
                f'or make use of the "from_file"-method.'
            )
            raise TypeError(msg)

        if parameter == "LAC":
            parameter = "light_attenuation"

        daily_params = ("light", "light_attenuation", "temperature", "aragonite")
        if parameter in daily_params:
            setattr(self, f"_{parameter}", set_value(value))
        elif parameter == "storm":
            years = set(self.dates.dt.year)
            self._storm_category = pd.DataFrame(data=value, index=years)
        else:
            msg = f"Entered parameter ({parameter}) not included. See documentation."
            raise ValueError(msg)
