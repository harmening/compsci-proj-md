
import numpy as np
# Fill these before you start the Simulation

#Substance to be simulated e.g NaCl 
Symbols = np.array(['Na','Cl'])

#Stochiometric Coefficients e.g. Na_1_Cl_1
Coefficients = np.array([1,1])

#Atomic Charges e.g. Na_1+_Cl_1-
Charges = np.array([1.0 ,-1.0])

#Number of Particles
N = 10

#Boxsize
L_x=0.1
L_y=0.1
L_z=0.1
#L = np.array([L_x, L_y, L_z])

#LJ Cutoff Radius
r_cut_LJ = 0.07

#Short-Range Potential Cutoff Radius
r_cut_coulomb = 0.07

#Accuracy Factor, the cutofferror is given by exp(-p)
p = 10.0

#Temperature 
T = 100 # Kelvin 

#Timestep
dt = 1e-3 # 1 ns

#Characetristic coupling time for Thermostat, must be larger than dt
tau = 1e-1
assert tau>dt, "tau must be larger than dt"

#switch-parameter for Lennard-Jones-Forces
switch_parameter = np.array([1,-1,0,0])

#distance where the switch-function kicks in (Lennard-Jones-Forces)
r_switch = 1.5


###############################################
# !!!  DO NOT CHANGE THE FOLLOWING LINES  !!! #
###############################################

# Summarizing Dimension in one array
L = np.array([L_x, L_y, L_z])

#Reassignment Probability
p_rea = dt/tau

#Coulomb interaction sigma
std = r_cut_coulomb/np.sqrt(2*p)

#K_cut
k_cut = 2*p/r_cut_coulomb

#number of Boxes to consider for LJ-Potential
n_boxes_LJ = np.ceil(r_cut_LJ/np.max(L)).astype(int) 

##number of Boxes to consider for short ranged Potential
n_boxes_short_range = ( np.ceil(r_cut_coulomb/np.max(L)) ).astype(int)

#largest values of k to consider for long range Potential
k_max_long_range = int(np.floor((k_cut*L[0])/(2*np.pi)))




