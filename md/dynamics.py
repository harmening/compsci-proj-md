import numpy as np
import math
from particle_interaction import coulomb
from particle_interaction import lennard_jones
from distribution import maxwellboltzmann
from neighbourlist import neighbourlist

class dynamics(object):

    def __init__(self):
        return

    def velocity_verlet_integrator(self,
                                   Positions,
                                   Velocities, 
                                   Forces, 
                                   Labels,
                                   Sigma, 
                                   Epsilon ,
                                   dt,
                                   L, 
                                   T,
                                   switch_parameter, 
                                   r_switch,
                                   neighbours_LJ,
                                   p_rea,
                                   coulomb,
                                   lennard_jones,
                                   d_Pos,
                                   thermostat):
        ''' The Verlocity Verlet Integrator
        Parameters:
        --------------
        thermostat: bool
            if True, sampling takes place in the NVT ensemble
            else sampling takes place in the NVE ensemble.
            
        Returns:
        -------------
        Updated Positions
        Updated Velocities
        Updated Forces
        '''       

        Forces_old = Forces

        Positions_new = Positions +Velocities*dt + Forces_old/(np.outer(Labels[:,0],np.ones(3))) *dt**2 

        #Implement PBC

        #use fmod instead of %, see, for further information see
        #https://docs.python.org/3/library/math.html#math.fmod
        Positions_new[:,0] = np.remainder(Positions_new[:,0],L[0])
        Positions_new[:,1] = np.remainder(Positions_new[:,1],L[1])
        Positions_new[:,2] = np.remainder(Positions_new[:,2],L[2])
        
        
        Forces_new = coulomb.compute_forces(d_Pos,
            Labels,
            L)+lennard_jones.compute_forces(
            Positions_new,
            Sigma, 
            Epsilon, 
            Labels,
            L, 
            switch_parameter, 
            r_switch,
            neighbours_LJ)
        
        Velocities_new = Velocities + (Forces_old+Forces_new)/(2*(np.outer(Labels[:,0],np.ones(3))))*dt
        
        if thermostat == True:
        
            #Andersen Thermostat
            N = np.size(Positions[:,0])
            m = Labels[:,0]

            #Draw Random Number for every Particle
            Rand = np.random.uniform(size =N) 

            #Check wich random numbers are smaller than the reassingment probability p_rea
            indexes = np.where(Rand<p_rea) 
            if np.size(indexes) is not 0: 

                #Reassign a new Velocity to the Correspoding Particles
                Velocities_new[indexes] = maxwellboltzmann().sample_distribution(N = np.size(indexes), m = m[indexes], T=T)        

            return Positions_new, Velocities_new, Forces_new
        
        else:
            return Positions_new, Velocities_new, Forces_new
    
    def Thermometer(self, Labels, Velocities,kB=0.0001987191):
        
        """ Compute the Instantaneos Temperature of a given Frame
        
        Parameters
        ------------
        Labels: Nx3 Array
            Array with one Row for each particle, containing masses, charges and chemical label repsectively
            
        Velocities: Nx3 Array
            Array with one Row for each particle, containing its velocities componentwise. 
           
        Returns
        -----------
        Temperatur: float
            The instantaneous Temperature of the System
        """
        m = Labels[:,0] #Masses
        N = np.size(m)
        M = np.sum(m) #Total Mass
        
        #Velocity of Center of Mass: (Sum_over_i (m_i*v_i) )/M
        CM = np.sum( np.reshape( np.repeat(m,3) ,(N,3) )*Velocities, 0)/M
        
        #remove components along external degrees of freedom
        internal_Velocities = Velocities-CM
        
        # T = 2/kB/N_df * <K>
        #<K> = Sum_over_i (m_i*v_i**2)/2
        # N_df = 3*N-3
        Temperature = np.sum(m*np.linalg.norm(internal_Velocities,axis = 1)**2 )/kB/(3*N-3) #Calculate the Actual Temperature

        return Temperature


    def steepest_descent(self,Positions, Forces,L, c):
        """Energy Minimization """

        Positions_new = Positions + Forces*c


        Positions_new[:,0] = np.remainder(Positions_new[:,0],(L[0]) )
        Positions_new[:,1] = np.remainder(Positions_new[:,1],(L[1]) )
        Positions_new[:,2] = np.remainder(Positions_new[:,2],(L[2]) )

        return Positions_new
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
