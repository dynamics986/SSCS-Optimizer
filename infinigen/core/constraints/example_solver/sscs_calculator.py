class SSCSCalculator:
    def __init__(self, norm_params=None):
        self.norm = norm_params or {
            "C_max": 25, "I_max": 500, "S_max": 8000, "F_max": 4000, "T_max": 5, "M_max": 50, "P_max": 40000
        }

    def compute(self, scene):
        # Suppose scene has methods to get the required metrics
        # These methods should return the respective counts or ratios

        N_cat = scene.get_category_count()
        N_inst = scene.get_instance_count()
        #R_inter = scene.get_interactive_category_ratio()
        E_spatial = scene.get_spatial_entropy()
        Floor_area = scene.get_floor_area()
        # Surface_area = scene.get_surface_area()

        # D_obj = scene.get_object_density(Floor_area)
        # D_inter = scene.get_interactive_object_density(Floor_area)
        # P_inter = scene.get_interactive_object_proportion()
        # N_itype = scene.get_interaction_type_count()
        # N_mat = scene.get_material_count()
        # P_avg = scene.get_avg_poly_count()

        S_OD = 0.45 * (N_cat / self.norm["C_max"]) + 0.55 * (N_inst / self.norm["I_max"])
        S_LC = 0.5 * E_spatial + 0.5 * (Floor_area / self.norm["F_max"])
        # S_FP = 0.8 * R_inter + 0.2 * (N_itype / self.norm["T_max"])
        # S_VD = 0.5 * (N_mat / self.norm["M_max"]) + 0.5 * (P_avg / self.norm["P_max"])

        S_OD = min(max(S_OD, 0), 1)
        S_LC = min(max(S_LC, 0), 1)
        # S_FP = min(max(S_FP, 0), 1)
        # S_VD = min(max(S_VD, 0), 1)
        print(f"Compute SSCS: \nS_OD: {S_OD:.3f}, S_LC: {S_LC:.3f}")
        print(f"E_spatial: {E_spatial:.3f}, Floor_area: {Floor_area:.3f}")
        SSCS = 0.5 * S_OD + 0.5 * S_LC
        return SSCS