'''
Class for the Molecular Dynamics Simulation
'''
import numpy as np
import PSE
from neighbourlist import neighbourlist
from particle_interaction import coulomb
from particle_interaction import lennard_jones
from dynamics import dynamics
from scipy.constants import epsilon_0
import sys
PSE = PSE.PSE

class System(object):
    """ This Class defines the Chemical Systems
    input must look as follows:
    
    e.g. NaCl
    
    Symbols = ['Na', Cl']  #Chemical Symbols of the types of Atmos
    
    Coeffcients = [1,1] #Stochiometric coefficients in the sum formula
    
    Charges = [1, -1] #Charges of the individual chemical species
    
    n = int #Number of Particles in the System
    
    Returns:
    ----------
    Nothing
    """
    def __init__(self,Symbols,Coefficients, Charges,n):
        self.Symbols = Symbols
        self.Coefficients = Coefficients
        self.Charges = Charges
        self.n = int(n)
        return
    
    def get_Labels(self):
        """Create the Nx3 Array Labels containing each Particles Mass, Charge and chemical Label """
        s = np.sum(self.Coefficients)
        m = np.zeros(self.n*s)
        q = np.zeros(self.n*s)
        chemical_labels  = np.zeros(self.n*s)
        size = np.size(self.Symbols)

        m[:self.n*self.Coefficients[0]] = PSE[ self.Symbols[0] ][1].astype('float64')
        for j in np.arange((np.size(self.Coefficients)-1)):
            m[self.n*np.cumsum(self.Coefficients)[j]:self.n*np.cumsum(self.Coefficients)[j+1]] = PSE[ self.Symbols[j+1] ][1].astype('float64')
        m *= 1.660539040e-27  # Correcting Unit, amu --> kg
        
        q[:self.n*self.Coefficients[0]] = self.Charges[0]
        for j in np.arange((np.size(self.Coefficients)-1)):
            q[self.n*np.cumsum(self.Coefficients)[j]:self.n*np.cumsum(self.Coefficients)[j+1]] = self.Charges[j+1]
        q *= 1.6021766208e-19 #Correcting Unit, 1 --> C


        index = np.zeros(np.size(self.Symbols))
        index = 2**np.arange(np.size(index))-1

        chemical_labels[:self.n*self.Coefficients[0]] = index[0]
        for j in np.arange((np.size(self.Coefficients)-1)):
            chemical_labels[self.n*np.cumsum(self.Coefficients)[j]:self.n*np.cumsum(self.Coefficients)[j+1]] = index[j+1]

        Labels  = np.zeros((self.n*s,3))
        Labels[:,0] = m
        Labels[:,1] = q
        Labels[:,2] =chemical_labels
        return Labels
    
    def get_LJ_parameter(self):
        
        index = np.zeros(np.size(self.Symbols))
        index = 2**np.arange(np.size(index))-1

        index = index.astype(int)
        Sigma = np.zeros((2*max(index)+1).astype(int) )
        Epsilon = np.zeros((2*max(index)+1).astype(int) )
        
        for i in index:
            l2_i = np.log2(i+1).astype(int)
            for j in index:
                l2_j = np.log2(j+1).astype(int)
                Sigma[i+j] = (PSE[self.Symbols[l2_i]][2].astype(float)+PSE[self.Symbols[l2_j]][2].astype(float)) /2.0

        for i in index:
            l2_i = np.log2(i+1).astype(int)
            for j in index:
                l2_j = np.log2(j+1).astype(int)
                Epsilon[i+j] = np.sqrt(PSE[self.Symbols[l2_i]][3].astype(float)*PSE[self.Symbols[l2_j]][3].astype(float))
        Epsilon *= (4184/6.022e23) #Convert Unit kcal/mol --> J
        return Sigma, Epsilon
    
    
class md(object):

    '''
    Initializes the md object.

    Parameters
        ----------
        
        positions: Nx3 Array 
            Array with N rows and 3 columns. Contains the Positions of each Particle component wise
            
        R : Nx1 Array 
            Array with N rows and 1 column. Contains the euclidic distances of each particle to the coordinate origin. 
            
        properties : Nx3 Array
            The number of rows represents the number of prticles
            The columns represent the properties [q, m, label]
            q = particle charge
            m = particle mass
            label = number to identify the type of atom
            
        velocities : Nx3 Array
            Array with N rows and 3 columns. Contains the Velocites of each Particle component wise
            
        box : 3xArray
           Array containing the lengths of the edges of the box. 
            
        Temperature : float
            Temperature of the System in Kelvin.
            
        std : int 
            Standart deviation of the Gauss Distribution, used in the Ewald Summation
            
        Sigma_LJ : Array
            Contains the Lennard Jones Parameter sigma for each interaction pair
        
        Epsilon_LJ : Array
             Contains the Lennard Jones Parameter epsilon for each interaction pair
             
        switch_parameter : 4x1 Array
            Contains the values of the parameters used in the switch polynomial
        
        r_switch: float
            Radius where the switch funtion is applied
        
        n_boxes_short_range: int
            Number of Boxes to consider for the short ranged interactions
        
        k_max_long_range: int
            Upper limit for any entry of any vektor k of the reciprocal space
        
        dt: int
            Timestep of the Simulation
            
        k_cut: float
            Cutoff-radius in reciprocal space
        
        p_rea: float
             Reassingment probability. Denotes the coupling strength to the thermostat. It is the probability with which a particle will undergo a velocity reassignment. 

    Returns
    -------
        nothing
    '''
    def __init__(self, 
                 positions,
                 properties, 
                 velocities,
                 forces,
                 box,
                 Temperature,
                 Sigma_LJ,
                 Epsilon_LJ, 
                 r_switch,
                 r_cut_LJ,
                 n_boxes_short_range,
                 dt,
                 p_rea,
                 p_error,
                 Symbols):
        #check input parameters
        self.positions=positions
        self.R=np.linalg.norm(self.positions)
        self.labels=properties
        self.velocities = velocities
        self.forces = forces
        self.L=box
        self.T= Temperature
        
        self.lennard_jones = lennard_jones()
        self.Sigma_LJ = Sigma_LJ
        self.Epsilon_LJ = Epsilon_LJ
        
        
        self.dt = dt
        self.p_rea = p_rea
        self.n_boxes_short_range= n_boxes_short_range
        
        # epsilon0 = (8.854 * 10^-12) / (36.938 * 10^-9) -> see Dimension Analysis
        self.coulomb = coulomb(n_boxes_short_range, box, p_error, epsilon0 = epsilon_0 / (36.938 * 10**-9))
        self.r_cut_coulomb, self.k_cut, self.std = self.coulomb.compute_optimal_cutoff(positions,properties,box,p_error)
        self.coulomb.n_boxes_short_range = np.ceil( self.r_cut_coulomb/self.L[0] ).astype(int)
        self.r_switch = r_switch
        self.r_cut_LJ = r_cut_LJ
        self.switch_parameter = self.__get_switch_parameter()
        self.neighbours_LJ, self.distances_LJ= neighbourlist().compute_neighbourlist(positions, box[0], self.r_cut_LJ)
        self.neighbours_coulomb, self.distances_coulomb= neighbourlist().compute_neighbourlist(positions, box[0], self.r_cut_coulomb)
        self.N = np.size(self.positions[:,0])
        self.Symbols = Symbols
        return
    
    @property
    def positions(self):
        return self._positions
    
    @positions.setter
    def positions(self,xyz):
        self._positions = xyz
        return
     
    @property
    def R(self):
        return self._R
    
    @R.setter
    def R(self,new_R):
        self._R = new_R
        return
    
    @property
    def velocities(self):
        return self._velocities
    
    @velocities.setter
    def velocities(self,xyz):
        self._velocities = xyz
        return
    
    @property
    def forces(self):
        return self._forces    
    
    @forces.setter
    def forces(self,xyz):
        self._forces = xyz 
        return
    
    @property
    def potential(self):
        return self._potential  
    
    @potential.setter
    def potential(self,xyz):
        self._potential = xyz
        return
    
    def __get_switch_parameter(self):
        A = np.array([ 
            [1, self.r_switch, self.r_switch**2, self.r_switch**3], 
            [1, self.r_cut_LJ, self.r_cut_LJ**2, self.r_cut_LJ**3],
            [0, 1, 2*self.r_switch, 3*self.r_switch**2], 
            [0, 0, 2, 6*self.r_switch]])
        switch_parameter = np.dot(np.linalg.inv(A), np.array([1,0,1,1]))
        return switch_parameter

    
    
    
    def get_neighbourlist_coulomb(self):
        """Compute the neighbourlist according to r_cut_coulomb and given configuration 
       
        
        Returns
        ..........
        
        neighbours: cell-linked list
            list at entry i contains all neighbours of particle i within cutoff-radius
        distances: cell-linked list
            list at entry i contains the distances to all neighbours of particle i within cutoff-radius
        """  
        neighbours, distances = neighbourlist().compute_neighbourlist(self.positions, self.L[0], self.r_cut_coulomb)
        return neighbours, distances
    
    def get_neighbourlist_LJ(self):
        """Compute the neighbourlist according to r_cut_coulomb and given configuration 
       
        
        Returns
        ..........
        
        neighbours: cell-linked list
            list at entry i contains all neighbours of particle i within cutoff-radius
        distances: cell-linked list
            list at entry i contains the distances to all neighbours of particle i within cutoff-radius
        """  
        neighbours, distances = neighbourlist().compute_neighbourlist(self.positions, self.L[0], self.r_cut_LJ)
        return neighbours, distances    
    
    
    # work in progress    
    def get_potential(self):
        """Compute the potential for the current configuration of the System
        
        Potential_total = Potential_Coulomb + Potential_Lennard_Jones
        
        Returns
        ..........
        
        Forces : float
            Number containg the Potential of the system with N particels 
        """        
        Potential = self.lennard_jones.compute_potential(sigma = self.Sigma_LJ,
                                                         epsilon = self.Epsilon_LJ, 
                                                         labels = self.labels,
                                                         neighbours = self.neighbours_LJ,
                                                         distances = self.distances_LJ)+(
        self.coulomb.compute_potential(labels = self.labels,
                                       positions = self.positions,
                                       neighbours = self.neighbours_coulomb,
                                       distances = self.distances_coulomb))
        
        return Potential
    
    
    def get_energy(self):
        
        Energy = self.lennard_jones.compute_energy(sigma = self.Sigma_LJ,
                                                   epsilon = self.Epsilon_LJ,
                                                   labels = self.labels,
                                                   neighbours = self.neighbours_LJ,
                                                   distances = self.distances_LJ)+(
        self.coulomb.compute_energy(labels = self.labels,
                                    positions = self.positions, 
                                    neighbours = self.neighbours_coulomb, 
                                    distances = self.distances_coulomb))
        return Energy
    
    
    
    
    
    
    def get_forces(self):
        """Compute the forces for the current configuration of the System
        
        F_total = F_Coulomb + F_Lennard_Jones
        
        Returns
        ..........
        
        Forces : N x 3 Array
            Array containg the Forces that act upon each particle component wise. 
        """
        Forces = self.lennard_jones.compute_forces(Positions =self.positions, 
                                                   Sigma =self.Sigma_LJ,
                                                   Epsilon = self.Epsilon_LJ, 
                                                   Labels =self.labels, 
                                                   L =self.L, 
                                                   switch_parameter = self.switch_parameter, 
                                                   r_switch = self.r_switch,
                                                   neighbours = self.neighbours_LJ)+(
        self.coulomb.compute_forces(Positions =self.positions,
                                      Labels = self.labels,
                                      L = self.L) )
        return Forces
    
    def propagte_system(self):
        """ Propagates the system by one timestep of length dt. Uses the Velocity Verlet Integrator and Andersen Thermostat.
        
        Returns 
        ----------
        Positions_new : N x 3 Array
            Array with N rows and 3 columns. Contains each particles positons component wise.
        
        Velocities_new : N x 3 Array
            Array with N rows and 3 columns. Contains each particles velocity component wise.
        
        Forces_new : N x 3 Array
            Array with N rows and 3 columns. Contains each the force acting upon each particle component wise.
        
        """
        Positions, Velocities, Forces = dynamics().velocity_verlet_integrator(self.positions,
                                                                               self.velocities, 
                                                                               self.forces, 
                                                                               self.labels,
                                                                               self.Sigma_LJ, 
                                                                               self.Epsilon_LJ,
                                                                               self.dt,
                                                                               self.L, 
                                                                               self.T,
                                                                               self.switch_parameter, 
                                                                               self.r_switch,
                                                                               self.neighbours_LJ,
                                                                               self.p_rea,
                                                                               self.coulomb,
                                                                               self.lennard_jones,
                                                                               thermostat = True)
        
        return Positions, Velocities, Forces
    
    def get_Temperature(self):
        """ Calculate the instantaneous Temperature of the given Configuration.
        
        Returns
        -----------
        Temperature : float
            The instantaneous Temperature.
        """
       
        T = dynamics().Thermometer(self.labels, self.velocities)
        return T
        
                         
    
    def get_traj(self, N_steps, Energy_save, Temperature_save, Frame_save, path):
        """Propagates the System unitil convergence is reached or the maximum Number of Steps is reached

        Parameters
        ----------------
        N_steps: int
            The number of steps the simulation will maximally run for.

        Energy_save: int
            The intervall at which energies are measured and saved.

        Temperature_save: int
            The intervall at which temperatures are measured and saved.

        Frame_save: int
            The intervall at which frames are created and saved. 

        Path: string
            Location where results will be saved.

        Returns
        -----------------
        "Simulation Completed"
        Results will be saved in the specified path. Files will be named as follows:
        Trajectory : traj.xyz
        Energies: Energies
        Temperature: Temperature

        """
        traj_file = ''.join([path,"\\traj.xyz"])
        Energy_file = ''.join([path,"\\Energies"])
        Temperature_file = ''.join([path,"\\Temperature"])
        string1 = (''.join([str(self.N), "\n", "\n"]))

        #write header
        myfile = open(traj_file,'w')
        myfile.write(str(self.N)+"\n"+"\n")
        myfile.close()

        frame = np.zeros((self.N), dtype=[('var1', 'U16'), ('var2',float), ('var3', float), ('var4',float)])
        frame['var1'] = self.Symbols[self.labels[:,2].astype(int)]

        #Positions in Angstroem
        frame['var2'] = self.positions[:,0]*1e10
        frame['var3'] = self.positions[:,1]*1e10
        frame['var4'] = self.positions[:,2]*1e10  

        myfile = open(traj_file,'ab')
        np.savetxt(myfile,frame, fmt = "%s %f8 %f8 %f8", )
        myfile.close()
        myfile = open(traj_file,'a')
        myfile.write(string1)
        myfile.close()

        Energy = np.zeros(np.ceil(N_steps/Energy_save).astype(int))
        Temperature = np.zeros(np.ceil(N_steps/Temperature_save).astype(int))

        counter_Energy = 0
        counter_Temperature = 0
        counter_Frame = 0
        E_index = -1

        for i in np.arange(N_steps):

            Positions_New, Velocities_New, Forces_New = self.propagte_system()
            self.positions = Positions_New
            self.velocities = Velocities_New
            self.forces = Forces_New
            self.neighbours_LJ  = self.get_neighbourlist_LJ()[0]

            counter_Energy += 1
            counter_Temperature += 1
            counter_Frame += 1

            #Save Energy
            if counter_Energy > Energy_save-1:
                E_index += 1
                Energy[E_index] = self.get_energy()
                counter_Energy = 0

            #Save Temperature
            if counter_Temperature > Temperature_save-1:
                Temperature[np.floor(i/Temperature_save).astype(int)] = self.get_Temperature()
                counter_Temperature = 0

            # Save Frame
            if counter_Frame > Frame_save-1 :
                #create frame
                frame = np.zeros((self.N), dtype=[('var1', 'U16'), ('var2',float), ('var3', float), ('var4',float)])
                frame['var1'] = self.Symbols[self.labels[:,2].astype(int)]

                #Positions in Angstroem
                frame['var2'] = self.positions[:,0]*1e10
                frame['var3'] = self.positions[:,1]*1e10
                frame['var4'] = self.positions[:,2]*1e10  

                #save frame
                myfile = open(traj_file,'ab')
                np.savetxt(myfile,frame, fmt = "%s %f8 %f8 %f8", )
                myfile.close()
                myfile = open(traj_file,'a')
                myfile.write(string1)
                myfile.close()

                counter_Frame = 0

            sys.stdout.write("\r")
            sys.stdout.write( ''.join([str(float(i+1)/N_steps*100), "% of steps completed"]))
            sys.stdout.flush()

        # save Energy       
        np.savetxt(Energy_file, Energy)
        # save Temperature         
        np.savetxt(Temperature_file, Temperature)

        print("Simulation Completed")
        return
    
    def minmimize_Energy(self,N_steps, threshold, Energy_save, Frame_save, constant, path):
        """Minimizes the Energy by steepest descent

        Parameters
        ----------------
        N_steps: int
            The number of steps the simulation will maximally run for.
            
        threshold: float
            if the line sum norm of the forces falls below the threshold, the minimization is completed

        Energy_save: int
            The intervall at which energies are measured and saved.

        Frame_save: int
            The intervall at which frames are created and saved. 
            
        constant: float
            The constant, the forces are multiplied with, to update the positions

        Path: string
            Location where results will be saved.

        Returns
        -----------------
        Means by which the minimization was completed.
        either "Energy converged" 
        or "Maximum Number of steps reached
        
        Results will be saved in the specified path. Files will be named as follows:
        Trajectory : traj.xyz
        Energies: Energies"""
        
        traj_file = ''.join([path,"\\traj_minimization.xyz"])
        Energy_file = ''.join([path,"\\Energies_minimization"])
        string1 = (''.join([str(self.N), "\n", "\n"]))

        #write header
        myfile = open(traj_file,'w')
        myfile.write(str(self.N)+"\n"+"\n")
        myfile.close()

        frame = np.zeros((self.N), dtype=[('var1', 'U16'), ('var2',float), ('var3', float), ('var4',float)])
        frame['var1'] = self.Symbols[self.labels[:,2].astype(int)]

        #Positions in Angstroem
        frame['var2'] = self.positions[:,0]*1e10
        frame['var3'] = self.positions[:,1]*1e10
        frame['var4'] = self.positions[:,2]*1e10  

        myfile = open(traj_file,'ab')
        np.savetxt(myfile,frame, fmt = "%s %f8 %f8 %f8", )
        myfile.close()
        myfile = open(traj_file,'a')
        myfile.write(string1)
        myfile.close()

        Energy = np.zeros(np.ceil(N_steps/Energy_save).astype(int))

        counter_Energy = 0
        counter_Frame = 0
        E_index = -1
        
        for i in np.arange(N_steps):
        
            #Update Positions
            Positions_new = dynamics().steepest_descent(self.positions,self.forces,self.L, constant)

            #Update Self
            self.positions = Positions_new
            self.neighbours_LJ = self.get_neighbourlist_LJ()[0]
            self.forces = self.get_forces()
            
            counter_Energy += 1
            counter_Frame += 1
            #Save Energy
            if counter_Energy > Energy_save-1:
                E_index += 1
                Energy[E_index] = self.get_energy()
                counter_Energy = 0

            # Save Frame
            if counter_Frame > Frame_save-1 :
                #create frame
                frame = np.zeros((self.N), dtype=[('var1', 'U16'), ('var2',float), ('var3', float), ('var4',float)])
                frame['var1'] = self.Symbols[self.labels[:,2].astype(int)]

                #Positions in Angstroem
                frame['var2'] = self.positions[:,0]*1e10
                frame['var3'] = self.positions[:,1]*1e10
                frame['var4'] = self.positions[:,2]*1e10  

                #save frame
                myfile = open(traj_file,'ab')
                np.savetxt(myfile,frame, fmt = "%s %f8 %f8 %f8", )
                myfile.close()
                myfile = open(traj_file,'a')
                myfile.write(string1)
                myfile.close()

                counter_Frame = 0
            
            #show Progress
            sys.stdout.write("\r")
            sys.stdout.write( ''.join([str(float(i+1)/N_steps*100), "% of steps completed"]))
            sys.stdout.flush()
            
            # Calculate norm
            norm_Forces = np.max(np.sum(np.abs(self.forces),1))
            
            if norm_Forces < threshold:
                #create frame
                frame = np.zeros((self.N), dtype=[('var1', 'U16'), ('var2',float), ('var3', float), ('var4',float)])
                frame['var1'] = self.Symbols[self.labels[:,2].astype(int)]

                #Positions in Angstroem
                frame['var2'] = self.positions[:,0]*1e10
                frame['var3'] = self.positions[:,1]*1e10
                frame['var4'] = self.positions[:,2]*1e10  

                #save frame
                myfile = open(traj_file,'ab')
                np.savetxt(myfile,frame, fmt = "%s %f8 %f8 %f8", )
                myfile.close()
                myfile = open(traj_file,'a')
                myfile.write(string1)
                myfile.close()
                
                # save Energy       
                np.savetxt(Energy_file, Energy)

                print("Energy Converged")
                return 
            
            
        # save Energy       
        np.savetxt(Energy_file, Energy)

        print("Maximum Number of Steps reached")
        return
