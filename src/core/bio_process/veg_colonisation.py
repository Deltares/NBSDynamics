from typing import Optional
import numpy as np
from src.core.base_model import ExtraModel
from src.core.common.constants_veg import Constants
from src.core.vegetation.veg_model import Vegetation
from src.core.hydrodynamics.delft3d import FlowFmModel


class Colonization(ExtraModel):
    """
    Colonization
    Colonisation method (1 = on bare substrate between max and min water levels, 2 = on bare substrate with mud content

    Colonization depends on ColMethod
    1. inundation (max, min water level, flooded only in max waterlevel: intertidal area)
    2. mud fraction in top layer: mud_frac>mud_colonization (NOT YET FULLY IMPLEMENTED!)

    """

    cir: Optional[np.ndarray] = None
    ma: Optional[np.ndarray] = None
    constants: Constants = Constants()

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.seed_loc = None

    def update(self, veg: Vegetation):
        """Update marsh cover after colonization (settlement)
        ONLY IF WE ARE IN THE RIGHT ETS!

        :param veg: vegetation
        :type vegetation: Vegetation
        """

        # # available locations for settlement
        Colonization.col_location(self, veg)
        # TODO check this!
        for loc in range(len(self.seed_loc)):
            if veg._cover[self.seed_loc[loc]] <= (1 - self.constants.iniCol_frac):
                veg.veg_age_frac[loc, 0] = self.constants.iniCol_frac
            else:
                pass

        veg.update_vegetation_characteristics(veg, veg_age_frac=veg.veg_age_frac)

    def col_location(self, veg):
        """new vegetation settlement

        :param veg: vegetation
        :type vegetation: Vegetation
        """
        # find seedling location in cells that have water depth only at max. water level
        # for random establishment extract random selection of seedling locations
        self.seed_loc = np.where(self.colonization_criterion(veg) == True)  # all possible locations for seedlings
        if self.constants.random == 0:
            self.seed_loc = self.seed_loc
        else:
            self.seed_loc = np.random.choice(self.seed_loc, round(
                len(self.seed_loc) / self.constants.random))  # locations where random settlement can occur

    def colonization_criterion(self, veg: Vegetation):
        """determine areas which are available for colonization

        :param veg: vegetation

        :type veg: Vegetation
        """
        # if self.constants.ColMethod == 1:
        self.colonization_inundation_range(veg)
        return self.cir
        # elif self.constants.ColMethod == 2:
        #     self.colonization_inundation_range(veg)
        #     self.mud_availability(veg)
        #     return np.logical_and(self.cir, self.ma) #matrix with true everywhere where vegetation is possible according to mud content and inundation

    def colonization_inundation_range(self, veg: Vegetation):
        """ Colonization Inundation range
        Args:
            veg (Vegetation): Vegetation
        """

        # # Calculations
        self.cir = np.ones(FlowFmModel.space.shape)
        self.cir = (self.cir_formula(veg.max_wl,
                                     veg.min_wl) == 1)  # true, false matrix look for cells that are flooded during high anf low water levels

    @staticmethod
    def cir_formula(max_water_level, min_water_level):

        return (max_water_level[max_water_level > 0] == 1) - (min_water_level[min_water_level > 0] == 1)

##TODO get information on mud in top layer from DFM
# def mud_availability(self, veg: Vegetation):
#     """ Colonization criterion for mud availability
#            Args:
#                veg (Vegetation): Vegetation
#     """
#     self.ma = np.ones(FlowFmModel.space.shape)
#     self.ma = veg.mud_fract > self.constants.mud_colonization(veg.veg_ls) #matrix with false and true
