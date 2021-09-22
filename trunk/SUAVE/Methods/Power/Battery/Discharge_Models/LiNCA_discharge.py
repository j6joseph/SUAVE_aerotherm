## @ingroup Methods-Power-Battery-Discharge
# LiNCA_discharge.py
# 
# Created: Apr 2021, M. Clarke

# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------
import SUAVE
from SUAVE.Core import  Units 
import numpy as np 
from scipy.integrate import  cumtrapz  

def LiNCA_discharge(battery,numerics): 
    """This is a discharge model for lithium-nickel-cobalt-aluminum oxide 18650 battery
       using a thevenin equavalent circuit with parameters taken from 
       pulse tests done by NASA Glen (referece below) of a Samsung (SDI 18650-30Q). 
     
       Assumtions:
       1) All battery modules exhibit the same themal behaviour.
       
       Source:  
       N/A 
        
       Inputs:
         battery. 
               I_bat             (max_energy)                          [Joules]
               cell_mass         (battery cell mass)                   [kilograms]
               Cp                (battery cell specific heat capacity) [J/(K kg)]
               h                 (heat transfer coefficient)           [W/(m^2*K)]
               t                 (battery age in days)                 [days]
               cell_surface_area (battery cell surface area)           [meters^2]
               T_ambient         (ambient temperature)                 [Degrees Celcius]
               T_current         (pack temperature)                    [Degrees Celcius]
               T_cell            (battery cell temperature)            [Degrees Celcius]
               E_max             (max energy)                          [Joules]
               E_current         (current energy)                      [Joules]
               Q_prior           (charge throughput)                   [Amp-hrs]
               R_growth_factor   (internal resistance growth factor)   [unitless] 
           
         inputs.
               I_bat             (current)                             [amps]
               P_bat             (power)                               [Watts]
       
       Outputs:
         battery.          
              current_energy                                           [Joules]
              cell_temperature                                         [Degrees Celcius]
              resistive_losses                                         [Watts] 
              load_power                                               [Watts]
              current                                                  [Amps]
              battery_voltage_open_circuit                                     [Volts]
              battery_thevenin_voltage                                 [Volts]
              charge_throughput                                        [Amp-hrs]
              internal_resistance                                      [Ohms]
              battery_state_of_charge                                          [unitless]
              depth_of_discharge                                       [unitless]
              battery_voltage_under_load                                        [Volts]   
        
    """
    
    # Unpack varibles 
    I_bat                    = battery.inputs.current
    P_bat                    = battery.inputs.power_in   
    cell_mass                = battery.cell.mass   
    electrode_area           = battery.cell.electrode_area
    Cp                       = battery.cell.specific_heat_capacity 
    h                        = battery.convective_heat_transfer_coefficient
    As_cell                  = battery.cell.surface_area 
    D_cell                   = battery.cell.diameter                     
    H_cell                   = battery.cell.height    
    P_ambient                = battery.ambient_pressure
    T_ambient                = battery.ambient_temperature 
    T_current                = battery.pack_temperature      
    T_cell                   = battery.cell_temperature  
    E_max                    = battery.max_energy
    R_growth_factor          = battery.R_growth_factor 
    E_current                = battery.current_energy 
    Q_prior                  = battery.charge_throughput  
    battery_data             = battery.discharge_performance_map 
    heat_transfer_efficiency = battery.heat_transfer_efficiency
    I                        = numerics.time.integrate  
    D                        = numerics.time.differentiate      
    
    # ---------------------------------------------------------------------------------
    # Compute battery electrical properties 
    # ---------------------------------------------------------------------------------
    
    # Calculate the current going into one cell  
    n_series          = battery.pack_config.series  
    n_parallel        = battery.pack_config.parallel
    n_total           = battery.pack_config.total
    Nn                = battery.module_config.normal_count            
    Np                = battery.module_config.parallel_count          
    n_total_module    = Nn*Np    
    I_cell            = I_bat/n_parallel
    
    # State of charge of the battery
    initial_discharge_state = np.dot(I,P_bat) + E_current[0]
    SOC_old =  np.divide(initial_discharge_state,E_max)
    SOC_old[SOC_old < 0.] = 0.    
    SOC_old[SOC_old > 1.] = 1.    
    DOD_old = 1 - SOC_old          
    
    # ---------------------------------------------------------------------------------
    # Compute battery cell temperature 
    # ---------------------------------------------------------------------------------
    # Determine temperature increase         
    sigma   = 100  # Electrical conductivity  Parameter Estimation and Model Discrimination for a Lithium-Ion Cell
    n       = 1
    F       = 96485      # C/mol Faraday constant    
    delta_S = -18046*(SOC_old)**6 + 52735*(SOC_old)**5 - 57196*(SOC_old)**4 + \
               28030*(SOC_old)**3 -6023*(SOC_old)**2 +  514*(SOC_old) -27
    
    i_cell         = I_cell/electrode_area # current intensity 
    q_dot_entropy  = -(T_cell)*delta_S*i_cell/(n*F)  # temperature in Kelvin  
    q_dot_joule    = (i_cell**2)/sigma                   # eqn 5 , D. Jeon Thermal Modelling ..
    Q_heat_gen     = (q_dot_joule + q_dot_entropy)*As_cell 
    q_joule_frac   = q_dot_joule/(q_dot_joule + q_dot_entropy)
    q_entropy_frac = q_dot_entropy/(q_dot_joule + q_dot_entropy)
    
    if n_total == 1: 
        # Using lumped model   
        Q_convec        = h*As_cell*(T_cell - T_ambient) 
        P_net           = Q_heat_gen - Q_convec
        P_net           = P_net*n_total 

    else: 
        # Chapter 7 pg 437-446 of Fundamentals of heat and mass transfer : Frank P. Incropera ... Incropera, Fran
        S_T             = battery.module_config.normal_spacing          
        S_L             = battery.module_config.parallel_spacing        
        coolant         = SUAVE.Attributes.Gases.Air()
        coolant.K       = battery.cooling_fluid.thermal_conductivity    
        coolant.Cp      = battery.cooling_fluid.specific_heat_capacity  
        coolant.V       = battery.cooling_fluid.discharge_air_cooling_flowspeed
        coolant.rho     = battery.cooling_fluid.density 
        coolant.nu      = battery.cooling_fluid.kinematic_viscosity    

        S_D = np.sqrt(S_T**2+S_L**2)
        if 2*(S_D-D_cell) < (S_T-D_cell):
            V_max = coolant.V*(S_T/(2*(S_D-D_cell)))
        else:
            V_max = coolant.V*(S_T/(S_T-D_cell))

        T        = (T_ambient+T_current)/2   
        Re_max   = V_max*D_cell/coolant.nu    
        if all(Re_max) > 10E2: 
            C = 0.35*((S_T/S_L)**0.2) 
            m = 0.6 
        else:
            C = 0.51
            m = 0.5 
            
        coolant.Pr      = coolant.compute_prandlt_number(T_ambient,P_ambient)
        coolant.Pr_wall = coolant.compute_prandlt_number(T,P_ambient)
        Nu              = C*(Re_max**m)*(coolant.Pr**0.36)*((coolant.Pr/coolant.Pr_wall)**0.25)           
        h               = Nu*coolant.K/D_cell
        Tw_Ti           = (T - T_ambient)
        Tw_To           = Tw_Ti * np.exp((-np.pi*D_cell*n_total_module*h)/(coolant.rho*coolant.V*Nn*S_T*coolant.Cp))
        dT_lm           = (Tw_Ti - Tw_To)/np.log(Tw_Ti/Tw_To)
        Q_convec        = heat_transfer_efficiency*h*np.pi*D_cell*H_cell*n_total_module*dT_lm 
        P_net           = Q_heat_gen*n_total_module - Q_convec 

    dT_dt     = P_net/(cell_mass*n_total_module*Cp)
    T_current = T_current[0] + np.dot(I,dT_dt)  

    # Power going into the battery accounting for resistance losses
    P_loss = n_total*Q_heat_gen
    P      = P_bat - np.abs(P_loss)      
    
    # Look up tables for variables as a function of temperature and SOC 
    V_oc = np.zeros_like(I_cell)
    R_Th = np.zeros_like(I_cell)  
    C_Th = np.zeros_like(I_cell)  
    R_0  = np.zeros_like(I_cell) 
    for i in range(len(SOC_old)):  
        # Open Circuit Voltage
        V_oc[i] = battery_data.V_oc_interp(T_cell[i], SOC_old[i])[0]
        
        # Thevenin Capacitance 
        C_Th[i] = battery_data.C_Th_interp(T_cell[i], SOC_old[i])[0]
        
        # Thevenin Resistance 
        R_Th[i] = battery_data.R_Th_interp(T_cell[i], SOC_old[i])[0]
        
        # Li-ion battery interal resistance
        R_0[i]  = battery_data.R_0_interp(T_cell[i], SOC_old[i])[0] 
    
    # Compute thevening equivalent voltage  
    V_Th = I_cell/(1/R_Th + C_Th*np.dot(D,np.ones_like(R_Th)))
    
    # Update battery internal and thevenin resistance with aging factor
    R_0_aged  = R_0 * R_growth_factor  
   
    # Calculate resistive losses
    Q_heat_gen = (I_cell**2)*(R_0_aged + R_Th)
      
    # Power going into the battery accounting for resistance losses
    P_loss = n_total*Q_heat_gen
    P = P_bat - np.abs(P_loss) 
    
    # ---------------------------------------------------------------------------------
    # Compute updates state of battery 
    # ---------------------------------------------------------------------------------   
    
    # Determine actual power going into the battery accounting for resistance losses
    E_bat = np.dot(I,P) 
            
    # Determine current energy state of battery (from all previous segments)          
    E_current = E_bat + E_current[0]
    
    # Determine new State of Charge 
    SOC_new = np.divide(E_current, E_max)
    SOC_new[SOC_new<0] = 0. 
    SOC_new[SOC_new>1] = 1.
    DOD_new = 1 - SOC_new
    
    # Determine voltage under load:
    V_ul   = V_oc - V_Th - (I_cell * R_0_aged)
     
    # Determine new charge throughput (the amount of charge gone through the battery)
    Q_total    = np.atleast_2d(np.hstack(( Q_prior[0] , Q_prior[0] + cumtrapz(I_cell[:,0], x = numerics.time.control_points[:,0])/Units.hr ))).T   
  
    # If SOC is negative, voltage under load goes to zero 
    V_ul[SOC_new < 0.] = 0.
    
    # Pack outputs
    battery.current_energy                      = E_current
    battery.cell_temperature                    = T_current   
    battery.pack_temperature                    = T_current
    battery.resistive_losses                    = P_loss
    battery.load_power                          = V_ul*n_series*I_bat
    battery.current                             = I_bat 
    battery.voltage_open_circuit                = V_oc*n_series
    battery.thevenin_voltage                    = V_Th*n_series
    battery.charge_throughput                   = Q_total*n_parallel  
    battery.cell_charge_throughput              = Q_total
    battery.internal_resistance                 = R_0*n_series 
    battery.state_of_charge                     = SOC_new
    battery.depth_of_discharge                  = DOD_new
    battery.voltage_under_load                  = V_ul*n_series  
    battery.cell_voltage_open_circuit           = V_oc
    battery.cell_current                        = I_cell 
    battery.heat_energy_generated               = Q_heat_gen*n_total_module 
    battery.cell_voltage_under_load             = V_ul
    battery.cell_joule_heat_fraction            = np.zeros_like(V_ul)
    battery.cell_entropy_heat_fraction          = np.zeros_like(V_ul)
    
    return battery