## @ingroupMethods-Noise-Fidelity_One-Noise_Tools
# decibel_arithmetic.py
# 
# Created: Oct 2020, M. Clarke

# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------

import numpy as np 
# -----------------------------------------------------------------------
# Decibel Arithmetic
# -----------------------------------------------------------------------
## @ingroupMethods-Noise-Fidelity_One-Noise_Tools
def pressure_ratio_to_SPL_arithmetic(p_pref_total):
    ''' This compute the total SPL given mutiple acoustic pressure ratios 
    of one of mutiple sources
    
    Assumptions:
        None

    Source:
        None

    Inputs:
        Pressure Ratios       [unitless]

    Outputs: 
        Sound Pressure Level  [decibel]

    Properties Used:
        N/A 
    
    '''
    SPL_total = 10*np.log10(np.sum(p_pref_total, axis = 1))
    return SPL_total

## @ingroupMethods-Noise-Fidelity_One-Noise_Tools
def SPL_arithmetic(SPL):
    '''This computes the total SPL from multiple sources 
    using decibel arithmetic  
    
    Assumptions:
        None

    Source:
        None

    Inputs:
        Sound Pressure Level        [decibel]

    Outputs: 
        Sound Pressure Level        [decibel]
    
    Properties Used:
        N/A 
    
    '''
    if SPL.ndim == 1:
        SPL_total = SPL 
    else:
        p_prefs   = 10**(SPL/10)
        SPL_total = 10*np.log10(np.sum(p_prefs, axis = 1))
        
    return SPL_total

## @ingroupMethods-Noise-Fidelity_One-Noise_Tools
def SPL_spectra_arithmetic(SPL):
    '''This computes the total SPL spectra from multiple sources 
    using decibel arithmetic  
    
    Assumptions:
        None

    Source:
        None

    Inputs:
        Sound Pressure Level        [decibel]

    Outputs: 
        Sound Pressure Level        [decibel]
    
    Properties Used:
        N/A 
    
    ''' 
    p_prefs   = 10**(SPL/10)
    SPL_total = 10*np.log10(np.sum(p_prefs, axis = 0))
        
    return SPL_total