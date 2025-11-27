from .Magneto import Magneto
import numpy as np
import os
import concurrent.futures
from concurrent.futures import as_completed
from tqdm import tqdm
from .Helmholtz import Helmholtz
import copy
from scipy.io import savemat
from datetime import datetime
from .Utility import cleanup
# Default settings for generating FEMM .fem magnetic problems.
SIM_DEFAULTS = {
    'units'     :   'millimeters',  # units
    'symmetry'  :   'axi',          # symmetry
    'precision' :   1e-8,           # precision
    'ddimension':   0,              # depth dimension
    'ang_cons'  :   30              # angular constraint
}

path_prefix = 'temp/'

class Testbench_B_Sweep():
    def __init__(self, freq=1e3, B_start=1e-6, B_end=3e-6, num_points=3, cleanup=False, **kwargs):
        self.__simulator = Magneto()
        self.freq = freq
        self.num_points = num_points
        self.Bs = np.linspace(B_start, B_end, num_points)
        self.cleanup = cleanup
        # Default settings for FEMM problems
        self.__sim_kwargs = {**{'freq' : self.freq}, **{k : kwargs.get(k, v) for k,v in SIM_DEFAULTS.items()}}
        self.path = None
        if not os.path.isdir("temp"):
            os.mkdir("temp")

    def __create_filename(self, sen, helm):
        sim_file_name = f"{sen.na}_{sen.ma}_sensor_{str(helm.B)}_T_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_{np.random.rand()}.fem"
        sim_file_name = sim_file_name.replace(" ", "")
        sim_file_name = sim_file_name.replace(":", "")

        return f"{path_prefix}{sim_file_name}"

    def simulate(self, sen):

        # build Helmholtz for given test flux density at a scale of 100x the (length+diameter) of the sensor.
        helm = Helmholtz(100 * (sen.ls + sen.ods), self.Bs[0], self.freq, 5, 1 )

        # Make deep copies of each sensor object to ensure they are identical
        sensor_air  = copy.deepcopy(sen)
        sensor_core = copy.deepcopy(sen)
        
        sensor_air.ma = 'Air'
        sensor_core.ma = sen.ma

        # Create initial .fem files for air and cored sensors
        self.__sim_objs = (sensor_air , helm)
        path_air =  self.__draw()
        self.__sim_objs = (sensor_core, helm)
        path_core = self.__draw()
        
        path_airs  = [path_air]
        path_cores = [path_core]

        ## Create Simulation Files
        print(f'GENERATING FEMM SWEEP FROM {self.Bs[0]} T to {self.Bs[-1]} T over {len(self.Bs)} points at {self.freq} Hz\n')
        # Duplicate the .fem files for air and cored sensors, creating an addition two .fem files for each field amplitude being simulated.
        print("STARTED GENERATING SIMULATION FILES\n")
        if len(self.Bs) > 1:
            for sensor, path, paths in zip([sensor_air, sensor_core], [path_air, path_core], [path_airs, path_cores]):
                self.__simulator.openfemm(True)
                self.__simulator.opendocument(str(path))
                for j, B in enumerate(self.Bs[1:]):

                    helm = Helmholtz( 100 * (sen.ls + sen.ods), B, self.freq, 5, 1 )
                    self.__simulator.mi.modifycircprop('icoil_transmitter', 1, helm.i)


                    sim_file_name = self.__create_filename(sen, helm)
                    self.__simulator.mi.saveas(sim_file_name)
                    paths.append(str(sim_file_name))
                
                self.__simulator.closefemm()
        print("FINISHED GENERATING SIMULATION FILES\n")
        #########################################################
        # CREATE FUTURES
        print("ASSIGNING SIMULATION FILES TO PROCESSES\n")
        pbar = tqdm(total=self.num_points*2, desc='Simulation Progress')  # Init pbar  # Increments counter
        with concurrent.futures.ProcessPoolExecutor(max_workers=None) as executor:
            # A list to store futures for data parsing

            futures_processes = []
            for path_air, path_core in zip(path_airs, path_cores):
               futures_processes.append(executor.submit(run,  sensor_air,  path_air ))
               futures_processes.append(executor.submit(run,  sensor_core, path_core))
            print("\nWAITING FOR SIMULATION PROCESSES TO COMPLETE...", end="")

            for _ in as_completed(futures_processes):
                pbar.update(n=1)  # Increments counter
            concurrent.futures.wait(futures_processes)

        print("SIMULATION COMPLETE\n")
        futures_air =  futures_processes[0::2]
        futures_core = futures_processes[1::2]
        #########################################################
        # PARSE
        print("EXTRACTING RESULTS...\n")
        B_air =  np.array([f.result()['B'] for f in futures_air])
        B_core = np.array([f.result()['B'] for f in futures_core])
        v_air =  np.array([f.result()['V'] for f in futures_air])
        v_core = np.array([f.result()['V'] for f in futures_core])

        # Calculate the sensitivity (in V per T per Hz) and the effective relative magnetic permeabilty of the coil at each operating con
        sensitivity = v_core / (B_air * self.freq)
        mu_eff = B_core / B_air

        # Performance a circuit analysis of the sensor in order to extract L and R parameters
        LR_PARAMS = self.__extract(path_air, path_core, self.freq, sen.odwc)

        # Results structure contains raw values as well as means.
        result = {
            'Name'              : sen.na,
            'V'                 : v_core,
            'B'                 : B_air,
            'Rair'              : LR_PARAMS['resistance_air'],
            'Rcore'             : LR_PARAMS['resistance_core'],
            'Lair'              : LR_PARAMS['inductance_air'],
            'Lcore'             : LR_PARAMS['inductance_core'],
            'sensitivities'     : sensitivity,
            'sensitivity_mean'  : np.mean(sensitivity),
            'sensitivity_std'   : np.std(sensitivity),
            'mu_effs'           : mu_eff,
            'mu_eff_mean'       : np.mean(mu_eff),
            'mu_eff_std'        : np.std(mu_eff),
            'path_air'          : path_airs,
            'path_core'         : path_cores
        }

        print("COIL MAGNETIC PARAMETERS:")
        print("Mean Sensitivity [Volts per (Tesla Hz)] = " + str(result['sensitivity_mean']) + " Standard Deviation = " + str(result['sensitivity_std']))
        print("Effective permeability = "+ str(result['mu_eff_mean']) + " Standard Deviation = " + str(result['mu_eff_std']))

        if self.cleanup:
            cleanup()

        return result

    def save_result(self,result):
        savemat(result['Name'] + f"_T_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mat", result)

    def __draw(self):

        self.__simulator.init(hide=True, **self.__sim_kwargs)

        ## Block Labels
        # Add block labels at the label coordinates for the sensor winding and core
        # Define these first avoids a bug
        for obj in self.__sim_objs:
            obj._label(self.__simulator)
        for obj in self.__sim_objs:
            obj._draw(self.__simulator)
        ## Boundary Conditions
        # Create Boundary Conditions
        self.__simulator.mi.makeABC()
        self.__simulator.mi.zoomnatural()

        ## Materials
        # Add materials for AIR used in simulation
        self.__simulator.mi.getmaterial( 'Air' )
        for obj in self.__sim_objs:
            self.__simulator.mi.addmaterial( * obj.material )
        for obj in self.__sim_objs:
            obj._properties( self.__simulator )
        
        self.__simulator.mi.zoomnatural()
        
        path = self.__create_filename( *self.__sim_objs )
        self.__simulator.mi.saveas( path )
        self.__simulator.closefemm()
        
        return path
    # Opens up all the resulting .ans files and extracts the simulated magnetic and circuit parameters
    def __extract(self, path_air, path_core, f, odwc):
        parameters = {}
        for ma, path in zip( ['air', 'core'], [path_air, path_core]):
            self.__simulator.openfemm(True)
            self.__simulator.opendocument(path)
            
            # Set the current of the sensor to a small value (1uA)
            i_sensor = 1e-6
            # Turn off the transmitter current (0A) so that no external field is
            # applied
            i_transmitter = 0

            self.__simulator.mi.modifycircprop('icoil_transmitter', 1, i_transmitter)
            self.__simulator.mi.modifycircprop('icoil_sensor', 1, i_sensor)
            self.__simulator.mi.addmaterial('Sensor',1,1,0,0,58,0,0,1,3,0,0,1,odwc)


            self.__simulator.mi.saveas('temp.fem')
            self.__simulator.mi.analyze()
            self.__simulator.mi.loadsolution()
            
            sensor_vals = self.__simulator.mo.getcircuitproperties('icoil_sensor')
            R = np.real(sensor_vals[1])/i_sensor
            L = np.imag(sensor_vals[1])/(2*np.pi*f*i_sensor)

            parameters.update({
                f'resistance_{ma}' : R,
                f'inductance_{ma}' : L
            })
            self.__simulator.mi.close()
            self.__simulator.mo.close()

        self.__simulator.closefemm()

        print("COIL ELECTRICAL PARAMETERS:")
        print("Sensor Air:")
        print(f"Resistance = {parameters['resistance_air']} [Ohms], Inductance = {parameters['inductance_air']} [Henries]")
        print("Sensor Core:")
        print(f"Resistance = {parameters['resistance_core']} [Ohms], Inductance = {parameters['inductance_core']} [Henries]\n")

        return parameters

def run( sen, path ):
    """
    Run method moved to module level to allow for multiprocessing 
    """
    simulator = Magneto()
    simulator.openfemm(True)

    simulator.opendocument(path)

    simulator.mi.analyze()
    simulator.mi.loadsolution()
    simulator.mo.zoomnatural()

    simulator.mo.selectblock(sen.lacr, sen.lacz)
    core_volume  = simulator.mo.blockintegral(10)
    Bz_avg_vol   = simulator.mo.blockintegral(9)
    B_Field_Core = np.abs(Bz_avg_vol/core_volume)

    sensor_vals = simulator.mo.getcircuitproperties('icoil_sensor')
    V_sensor = abs(sensor_vals[1])

    result = {
        'B'     : B_Field_Core,
        'V'     : V_sensor,
        'path'  : path   
    }
    
    simulator.closefemm()
    
    return result
