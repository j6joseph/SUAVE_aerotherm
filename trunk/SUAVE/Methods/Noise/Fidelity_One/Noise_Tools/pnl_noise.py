## @ingroupMethods-Noise-Fidelity_One-Noise_Tools
# pnl_noise.py
# 
# Created:  Jul 2015, C. Ilario
# Modified: Jan 2016, E. Botero

# ----------------------------------------------------------------------
#  Imports
# ---------------------------------------------------------------------
import numpy as np

# ----------------------------------------------------------------------
#  PNL Noise
# ---------------------------------------------------------------------

## @ingroupMethods-Noise-Fidelity_One-Noise_Tools
def pnl_noise (SPL):
    """This method calculates de Perceived Noise Level PNL from a 1/3 octave band noise spectra
 
    Assumptions:
        None

    Source:
        None
 
    Inputs:
        SPL - Sound Pressure Level in 1/3 octave band  [dB]
   
    Outputs:
        PNL - Perceived Noise Level                    [dB]
   
    Properties Used:
        N/A    
    """
   

    #Definition of the noisineess matrix for each octave band
    noy = [[1, 50, 91, 64, 52, 49, 55, 0.043478, 0.030103, 0.07952, 0.058098],
            [2,	63, 85.9, 60, 51, 44, 51, 0.04057, 0.030103, 0.06816, 0.058098],
            [3,	80, 87.3, 56, 49, 39,	46,	0.036831, 0.030103, 0.06816, 0.052288],
            [4,	100, 	79.9,	53,	47,	34,	42,	0.036831, 0.030103, 0.05964, 0.047534],
            [5,	125, 	79.8,	51,	46,	30,	39,	0.035336, 0.030103, 0.053013, 0.043573],
            [6,	160, 	76,  	48,	45,	27,	36,	0.033333, 0.030103, 0.053013, 0.043573],
            [7,	200, 	74,  	46,	43,	24,	33,	0.033333, 0.030103, 0.053013, 0.040221],
            [8,	250, 	74.9,	44,	42,	21,	30,	0.032051, 0.030103, 0.053013, 0.037349],
            [9,	315, 	94.6,	42,	41,	18,	27,	0.030675, 0.030103, 0.053013, 0.034859],
            [10, 400, 9999999, 40, 40, 16, 25, 0.030103, 0, 0.053013, 0.034859],
            [11, 500,  9999999,	40,	40,	16,	25,	0.030103, 0, 0.053013, 0.034859],
            [12, 630,  9999999,	40,	40,	16,	25,	0.030103, 0, 0.053013, 0.034859],
            [13, 800 , 9999999,	40,	40,	16,	25,	0.030103, 0, 0.053013, 0.034859],
            [14, 1000, 9999999,	40,	40,	16,	25,	0.030103, 0, 0.053013, 0.034859],
            [15, 1250, 9999999,	38,	38,	15,	23,	0.030103, 0, 0.05964, 0.034859],
            [16, 1600, 9999999,	34,	34,	12,	21,	0.02996, 0, 0.053013, 0.040221],
            [17, 2000, 9999999,	32,	32,	9,	18,	0.02996, 0, 0.053013, 0.037349],
            [18, 2500, 9999999,	30,	30,	5,	15,	0.02996, 0, 0.047712, 0.034859],
            [19, 3150, 9999999,	29,	29,	4,	14,	0.02996, 0, 0.047712, 0.034859],
            [20, 4000, 9999999,	29,	29,	5,	14,	0.02996, 0, 0.053013, 0.034859],
            [21, 5000, 9999999,	30,	30,	6,	15,	0.02996, 0, 0.053013, 0.034859],
            [22, 6300, 9999999, 31,	31,	10,	17,	0.02996, 0, 0.06816, 0.037349],
            [23, 8000, 44.3, 37, 34, 17, 23, 0.042285, 0.02996, 0.07952, 0.037349],
            [24, 10000, 50.7, 41, 37, 21, 29, 0.042285,	0.02996, 0.05964, 0.043573]]

    
    # Defining the necessary arrays for the calculation
    nsteps  = len(SPL)
    SPL_noy = np.zeros((nsteps,24))
    PNL     = np.zeros(nsteps)
    
    #-------------------------------------------
    # STEP 1 - Convert SPL to Perceived Noisiness
    #-------------------------------------------  
    for j in range(0,nsteps):
    
        for i in range(0,23):
            if SPL[j][i]>=noy[1][2]:
                SPL_noy[j][i] = 10**(noy[i][8]*(SPL[j][i]-noy[i][4]))
                
            if SPL[j][i]>=noy[i][3] and SPL[j][i]<noy[i][2]:
                SPL_noy[j][i] = 10**(noy[i][7]*(SPL[j][i]-noy[i][3]))
                
            if SPL[j][i]>=noy[i][6] and SPL[j][i]<noy[i][3]:
                SPL_noy[j][i] = 0.3*(10**(noy[i][10]*(SPL[j][i]-noy[i][6])))
                
            if SPL[j][i]>=noy[i][5] and SPL[j][i]<noy[i][6]:
                SPL_noy[j][i] = 0.1*(10**(noy[i][9]*(SPL[j][i]-noy[i][5])))
            
        #-------------------------------------------  
        # STEP 2 - Combine perceived noiseness values  
        #-------------------------------------------
        max_noy = np.max(SPL_noy[j][:])            
        Perceived_noisinees = 0.85*max_noy+0.15*np.sum(SPL_noy[j][:])
        
        #-----------------------------------------------------------------
        # STEP 3 - Convert Perceived Noiseness into Perceived Noise Level
        #------------------------------------------------------------------    
        if Perceived_noisinees==0:
            Perceived_noisinees = 0.0625
        PNL[j] = 40+(10/np.log10(2))*np.log10(Perceived_noisinees)
        
    return (PNL)