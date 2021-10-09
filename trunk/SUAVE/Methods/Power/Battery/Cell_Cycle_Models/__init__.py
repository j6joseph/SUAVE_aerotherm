## @defgroup Methods-Power-Battery-State_Estimation_Models State_Estimation_Models
# Functions to evaluate battery state variables
# @ingroup Methods-Power-Battery

from .LiNCA_cell_cycle_model         import compute_NCA_cell_state_variables
from .LiNiMnCoO2_cell_cycle_model    import compute_NMC_cell_state_variables