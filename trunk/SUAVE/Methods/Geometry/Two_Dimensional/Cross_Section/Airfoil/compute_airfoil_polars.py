## @ingroup Methods-Geometry-Two_Dimensional-Cross_Section-Airfoil
# compute_airfoil_polars.py
# 
# Created:  Mar 2019, M. Clarke
# Modified: Mar 2020, M. Clarke
#           Jan 2021, E. Botero

# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------

import SUAVE
from SUAVE.Core               import Data , Units
from SUAVE.Methods.Aerodynamics.AERODAS.pre_stall_coefficients import pre_stall_coefficients
from SUAVE.Methods.Aerodynamics.AERODAS.post_stall_coefficients import post_stall_coefficients 
from .import_airfoil_geometry import import_airfoil_geometry 
from .import_airfoil_polars   import import_airfoil_polars 
from scipy.interpolate        import RectBivariateSpline
import numpy as np

## @ingroup Methods-Geometry-Two_Dimensional-Cross_Section-Airfoil
def compute_airfoil_polars(a_geo,a_polar):
    """This computes the lift and drag coefficients of an airfoil in stall regimes using pre-stall
    characterstics and AERODAS formation for post stall characteristics. This is useful for 
    obtaining a more accurate prediction of wing and blade loading. Pre stall characteristics 
    are obtained in the from of a text file of airfoil polar data obtained from airfoiltools.com
    
    Assumptions:
    Uses AERODAS forumatuon for post stall characteristics 

    Source:
    Models of Lift and Drag Coefficients of Stalled and Unstalled Airfoils in Wind Turbines and Wind Tunnels
    by D Spera, 2008

    Inputs:
    propeller. 
        hub_radius         [m]
        tip_radius         [m]
        chord_distribution [unitless]
    airfoils                <string>
           

    Outputs:
    airfoil_data.
        cl_polars          [unitless]
        cd_polars          [unitless]      
        aoa_sweep          [unitless]
    
    Properties Used:
    N/A
    """  
    
    num_airfoils = len(a_geo)
    num_polars   = len(a_polar[0])
    if num_polars < 3:
        raise AttributeError('Provide three or more airfoil polars to compute surrogate')

    # read airfoil geometry  
    airfoil_data = import_airfoil_geometry(a_geo)

    # Get all of the coefficients for AERODAS wings
    AoA_sweep_deg = np.linspace(-14,90,105)
    CL = np.zeros((num_airfoils,num_polars,len(AoA_sweep_deg)))
    CD = np.zeros((num_airfoils,num_polars,len(AoA_sweep_deg)))
    

    CL_surs = Data()
    CD_surs = Data()    
    
    # Create an infinite aspect ratio wing
    geometry              = SUAVE.Components.Wings.Wing()
    geometry.aspect_ratio = np.inf
    geometry.section      = Data()
    
    # Create dummy settings and state
    settings = Data()
    state    = Data()
    state.conditions = Data()
    state.conditions.aerodynamics = Data()
    state.conditions.aerodynamics.pre_stall_coefficients = Data()
    state.conditions.aerodynamics.post_stall_coefficients = Data()

    # AERODAS 
    for i in range(num_airfoils):
        
        # Modify the "wing" slightly:
        geometry.thickness_to_chord = airfoil_data.thickness_to_chord[i]
        
        for j in range(num_polars):
            
            # read airfoil polars 
            airfoil_polar_data = import_airfoil_polars(a_polar)
            airfoil_cl         = airfoil_polar_data.lift_coefficients[i,j] 
            airfoil_cd         = airfoil_polar_data.drag_coefficients[i,j] 
            airfoil_aoa        = airfoil_polar_data.angle_of_attacks  
            
            # computing approximate zero lift aoa
            airfoil_cl_plus = airfoil_cl[airfoil_cl>0]
            idx_zero_lift = np.where(airfoil_cl == min(airfoil_cl_plus))[0][0]
            A0  = airfoil_aoa[idx_zero_lift] * Units.degrees
            

            # max lift coefficent and associated aoa
            CL1max = np.max(airfoil_cl)
            idx_aoa_max_prestall_cl = np.where(airfoil_cl == CL1max)[0][0]
            ACL1 = airfoil_aoa[idx_aoa_max_prestall_cl] * Units.degrees

            # computing approximate lift curve slope
            linear_idxs = [int(np.where(airfoil_aoa==0)[0]),int(np.where(airfoil_aoa==4)[0])]
            cl_range = airfoil_cl[linear_idxs]
            aoa_range = airfoil_aoa[linear_idxs] * Units.degrees
            S1 = (cl_range[1]-cl_range[0])/(aoa_range[1]-aoa_range[0])

            # max drag coefficent and associated aoa
            CD1max  = np.max(airfoil_cd) 
            idx_aoa_max_prestall_cd = np.where(airfoil_cd == CD1max)[0][0]
            ACD1   = airfoil_aoa[idx_aoa_max_prestall_cd] * Units.degrees     
            
            # Find the point of lowest drag and the CD
            idx_CD_min = np.where(airfoil_cd==min(airfoil_cd))[0][0]
            ACDmin     = airfoil_aoa[idx_CD_min] * Units.degrees
            CDmin      = airfoil_cd[idx_CD_min]    
            AoA_sweep_radians = AoA_sweep_deg*Units.degrees
            
            # Setup data structures for this run
            ones = np.ones_like(AoA_sweep_radians)
            settings.section_zero_lift_angle_of_attack                = A0
            state.conditions.aerodynamics.angle_of_attack             = AoA_sweep_radians * ones 
            geometry.section.angle_attack_max_prestall_lift           = ACL1 * ones 
            geometry.pre_stall_maximum_drag_coefficient_angle         = ACD1 * ones 
            geometry.pre_stall_maximum_lift_coefficient               = CL1max * ones 
            geometry.pre_stall_maximum_lift_drag_coefficient          = CD1max * ones 
            geometry.section.minimum_drag_coefficient                 = CDmin * ones 
            geometry.section.minimum_drag_coefficient_angle_of_attack = ACDmin
            geometry.pre_stall_lift_curve_slope                       = S1
            
            # Get prestall coefficients
            CL1, CD1 = pre_stall_coefficients(state,settings,geometry)
            
            # Get poststall coefficents
            CL2, CD2 = post_stall_coefficients(state,settings,geometry)
            
            # Take the maxes
            CL_ij = np.fmax(CL1,CL2)
            CL_ij[AoA_sweep_radians<=A0] = np.fmin(CL1[AoA_sweep_radians<=A0],CL2[AoA_sweep_radians<=A0])
            
            CD_ij = np.fmax(CD1,CD2)
            
            # Pack this loop
            CL[i,j,:] = CL_ij
            CD[i,j,:] = CD_ij
           
        CL_sur = RectBivariateSpline(airfoil_polar_data.reynolds_number[i],AoA_sweep_radians, CL[i,:,:])  
        CD_sur = RectBivariateSpline(airfoil_polar_data.reynolds_number[i],AoA_sweep_radians, CD[i,:,:])   
        
        CL_surs[a_geo[i]]  = CL_sur
        CD_surs[a_geo[i]]  = CD_sur       
      
    airfoil_data.angle_of_attacks              = AoA_sweep_radians
    airfoil_data.lift_coefficient_surrogates   = CL_surs
    airfoil_data.drag_coefficient_surrogates   = CD_surs 
    
    return airfoil_data

 