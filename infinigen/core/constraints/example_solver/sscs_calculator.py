import numpy as np
from infinigen.core.scene import Scene

class SSCSCalculator:
    def __init__(self, norm_params=None):
        self.norm = norm_params or {
            "C_max": 25, "I_max": 500, "T_max": 5, "M_max": 50, "P_max": 40000
        }

    def compute(self, scene):
        # Suppose scene has methods to get the required metrics
        # These methods should return the respective counts or ratios

        N_cat = scene.get_category_count()
        N_inst = scene.get_instance_count()
        R_inter = scene.get_interactive_category_ratio()
        ## D_obj = scene.get_object_density()
        E_spatial = scene.get_spatial_entropy()
        Floor_area = scene.get_floor_area() # 800
        Surface_area = scene.get_surface_area()
        ## D_inter = scene.get_interactive_object_density()
        ## P_inter = scene.get_interactive_object_proportion()
        N_itype = scene.get_interaction_type_count()
        N_mat = scene.get_material_count()
        P_avg = scene.get_avg_poly_count()

        OD = 0.4 * (N_cat / self.norm["C_max"]) + 0.3 * (N_inst / self.norm["I_max"]) + 0.3 * R_inter
        LC = 0.5 * E_spatial + 0.5 * (Surface_area / 8000)
        FP = N_itype / self.norm["T_max"]
        VD = 0.5 * (N_mat / self.norm["M_max"]) + 0.5 * (P_avg / self.norm["P_max"])

        OD = min(max(OD, 0), 1)
        LC = min(max(LC, 0), 1)
        FP = min(max(FP, 0), 1)
        VD = min(max(VD, 0), 1)

        SSCS = 0.4 * OD + 0.25 * LC + 0.1 * FP + 0.25 * VD
        return SSCS 