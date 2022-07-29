from typing import Optional

import numpy as np

from src.biota_models.mangroves.bio_process.mangrove_hydro_morphodynamics import (
    Hydro_Morphodynamics,
)
from src.biota_models.mangroves.model.mangrove_constants import MangroveConstants
from src.biota_models.mangroves.model.mangrove_model import Mangrove
from src.core.base_model import ExtraModel

class Mangrove_Mortality(ExtraModel):
    """Mortality"""


    def update(self, mangrove: Mangrove, ets):
        mort_mark = Mangrove_Mortality.determine_stress(self, mangrove)

        if ets == (mangrove.constants.t_eco_year - 1):
            mangrove.mort = mangrove.mort + mort_mark # cells with suppressed growth


        # relative hydroperiod & competition
        # die if I*C <= 0.5
        # average I and C over time

        ## Step 0: Adjust the num to 0 if Inundation <=0.5 & Mort_mark == 5

            while any(mangrove.mort == 5):

                mort_temp = np.zeros(mangrove.stem_num.shape)
                mort_temp[mangrove.mort == 5] = 1 #set to one, where mortality status is 5
                mort_temp[np.tile(mangrove.I[:, -1].reshape(-1, 1), (mort_temp.shape[1])) <= 0.5] = mort_temp[np.tile(mangrove.I[:, -1].reshape(-1, 1), (mort_temp.shape[1])) <= 0.5] + 0.5
                mangrove.stem_num[mort_temp == 1.5] = 0
                mort_temp[mangrove.stem_num == 0] = 0 #set back to zeros is no vegetation present in cell
                mort_temp[mort_temp == 0.5] == 0
                mangrove.mort[np.sum(mort_temp, axis=1) == 0] = 0

                 # Step 2: Kill the mangroves cell by cell

                k = np.where(np.sum(mort_temp, axis=1) > 1)
                in_s = np.zeros(len(mangrove.stem_num))
                in_s[k] = np.mean(mangrove.I, axis=1)[k] # inundation stress
                in_s_inverse = 1/in_s

                remove = np.tile(np.round_(mangrove.constants.Mort_plant/(in_s*sum(in_s_inverse))).reshape(-1, 1),  (mangrove.stem_num.shape[1]) )
                remove[np.isnan(remove) == True] = 0
                remove[remove > mangrove.stem_num] = mangrove.stem_num[remove > mangrove.stem_num]
                mangrove.stem_num = mangrove.stem_num - remove
                self.bio_total_cell = Mangrove_Mortality.competition_stress(self, mangrove) # recalculate total biomass
                mangrove.mort[(mangrove.C*np.mean(mangrove.I, axis=1))>0.5] = 4

                k2 = np.where(np.sum(mort_temp, axis=1) == 1)
                mangrove.stem_num[k2] = mangrove.stem_num[k2] - mangrove.constants.Mort_plant
                Mangrove_Mortality.competition_stress(self, mangrove)  # recalculate total biomass
                mangrove.mort[(mangrove.C * np.mean(mangrove.I, axis=1)) > 0.5] = 4




    def determine_stress(self, mangrove: Mangrove):

        Mangrove_Mortality.inundation_stress(self, mangrove)
        Mangrove_Mortality.competition_stress(self, mangrove)
        if mangrove.I.ndim > 1:
            Av_I = np.mean(mangrove.I, axis=1)
        else:
            Av_I = mangrove.I

        stress = mangrove.C * Av_I # Ave_I * last_C
        mort_mark = np.zeros(stress.shape)
        mort_mark[stress<=0.5] = 1

        return mort_mark



    def inundation_stress(self, mangrove: Mangrove):
        P = mangrove.inun_rel #relative hydroperiod
        I_current = mangrove.constants.a * P**2 + mangrove.constants.b * P + mangrove.constants.c
        I_current[I_current<0] = 0
        if mangrove.stem_num.shape[1] == 1:
            mangrove.I = I_current.reshape(-1, 1)
        else:
            mangrove.I = np.column_stack((mangrove.I, I_current))

    def competition_stress(self, mangrove: Mangrove):

        mangrove.C = 1/(1+ np.exp(mangrove.constants.d*(mangrove.B_05 - mangrove.bio_total_cell)))
