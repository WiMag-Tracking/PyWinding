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
import matplotlib.pyplot as plt
import matplotlib as mpl
from sciform import Formatter
from .Utility import cleanup
mpl.rcParams['axes.formatter.useoffset'] = False


sform = Formatter(
    round_mode="sig_fig", exp_mode="engineering", ndigits=6
)


# Default settings for generating FEMM .fem magnetic problems.
SIM_DEFAULTS = {
    'units'     :   'millimeters',  # units
    'symmetry'  :   'axi',          # symmetry
    'precision' :   1e-8,           # precision
    'ddimension':   0,              # depth dimension
    'ang_cons'  :   30              # angular constraint
}

path_prefix = 'temp/'

# A testbench class to perform a magnitude sweep of a user defined coil design
# If no initialisers are provided by the user then the default stimulus frequency is 1000 Hz and evaluates the sensor over three flux density levels between 1 and 3 uT
class Testbench_B_Sweep():
    def __init__(self, freq=1e3, B_start=1e-6, B_end=3e-6, num_points=3, **kwargs):
        self.__simulator = Magneto()
        self.freq = freq
        self.num_points = num_points
        self.Bs = np.linspace(B_start, B_end, num_points)
        self.cleanup = cleanup
        # Default settings for FEMM problems
        self.__sim_kwargs = {**{'freq' : self.freq}, **{k : kwargs.get(k, v) for k,v in SIM_DEFAULTS.items()}}
        self.path = None
        self.results = None
        if not os.path.isdir("temp"):
            os.mkdir("temp")

    def __create_filename(self, sen, helm):
        sim_file_name = f"{sen.na}_{sen.ma}_sensor_{str(helm.B)}_T_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_{np.random.rand()}.fem"
        sim_file_name = sim_file_name.replace(" ", "")
        sim_file_name = sim_file_name.replace(":", "")

        return f"{path_prefix}{sim_file_name}"

    def simulate(self, sen, clean_up_femm=True):

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
        print("STARTED GENERATING SIMULATION FILES")
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
        print("FINISHED GENERATING SIMULATION FILES")

        print("ASSIGNING SIMULATION FILES TO PROCESSES")

        #########################################################
        # Distribute the simulations to different processes on the machine
        # All available CPU cores will be used by default.
        with concurrent.futures.ProcessPoolExecutor(max_workers=None) as executor:
            # A list to store futures for data parsing
            futures_processes = []
            for path_air, path_core in zip(path_airs, path_cores):
               futures_processes.append(executor.submit(run,  sensor_air,  path_air ))
               futures_processes.append(executor.submit(run,  sensor_core, path_core))
            print("WAITING FOR SIMULATION PROCESSES TO COMPLETE...")
            pbar = tqdm(total=self.num_points * 2, desc='Simulation Progress')  # Init pbar  # Increments counter
            for _ in as_completed(futures_processes):
                pbar.update(n=1)  # Increments counter
        pbar.close()

        print("SIMULATION COMPLETE")
        futures_air =  futures_processes[0::2]
        futures_core = futures_processes[1::2]
        #########################################################
        # PARSE
        print("EXTRACTING FIELD RESULTS...", end='')
        B_air =  np.array([f.result()['B'] for f in futures_air])
        B_core = np.array([f.result()['B'] for f in futures_core])
        v_air =  np.array([f.result()['V'] for f in futures_air])
        v_core = np.array([f.result()['V'] for f in futures_core])
        # Calculate the sensitivity (in V per T per Hz) and the effective relative magnetic permeabilty of the coil at each operating con
        sensitivity = v_core / (B_air * self.freq)
        mu_eff = B_core / B_air
        print("DONE")

        print("EXTRACTING COIL LR PARAMETERS...", end='')
        # Performance a circuit analysis of the sensor in order to extract L and R parameters
        LR_PARAMS = self.__extract(path_air, path_core, self.freq, sen.odwc)
        print("DONE")

        # Results structure contains raw values as well as means.
        self.results = {
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
            'paths_air'          : path_airs,
            'paths_core'         : path_cores
        }

        if clean_up_femm is True:
            cleanup()

        return self.results

    def save_results(self):
        if self.results is not None:
            save_path = self.results['Name'] + f"_T_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mat"
            print("\nSAVING RESULTS TO", save_path)
            savemat(save_path, self.results)
        else:
            print("No results saved, need to run simulation first.")

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

        return parameters

    def print_results(self):
        if self.results is not None:
            print("\nCOIL MAGNETIC PARAMETERS:")
            print("Mean Sensitivity (core) = " + ("%s [volts per tesla per hertz)]" % sform(self.results['sensitivity_mean'])))
            print("Sensitivity standard Deviation = " + ("%s" % sform(self.results['sensitivity_std'])))
            print("Effective permeability μ (core)= " + ("%s" % sform(self.results['mu_eff_mean'])))
            print("Standard Deviation = " + ("%s" % sform(self.results['mu_eff_std'])))

            print("\nCOIL ELECTRICAL PARAMETERS:")

            print("Resistance (air): %s [ohms]" % sform(self.results['Rair']))
            print("Resistance (core): %s [ohms]" % sform(self.results['Rcore']))
            print("Inductance (air): %s [henries]" % sform(self.results['Lair']))
            print("Inductance (core): %s [henries]" % sform(self.results['Lcore']))
        else:
            print("No results saved, need to run simulation first.")

    def plot_results(self):
        if self.results is not None:
            ## Plot the sensor response over the applied field
            plt.figure()
            plt.plot(self.results['B'], self.results['V'], 'bo')
            plt.xlabel("Applied magnetic flux density magnitude [T]")
            plt.ylabel("Voltage amplitude [V]")
            plt.title("Sensor voltage vs applied magnetic flux density")
            left = self.results['B'][0]
            top = self.results['V'][-1]
            plt.text(left, top, "Mean Sensitivity [V/(T.Hz)] = " + '%.7f' % (self.results['sensitivity_mean']))
            plt.grid(True)
            # ax.get_yaxis().get_major_formatter().set_useOffset(False)
            plt.show()

            # Plot the sensor sensitivity [in V/(T.Hz)] vs. the applied magnetic field
            plt.figure()
            plt.plot(self.results['B'], self.results['sensitivities'], 'bo')
            plt.xlabel("Applied magnetic flux density magnitude [T]")
            plt.ylabel("Coil sensitivity [V/(T.Hz)]")
            plt.title("Coil sensitivity vs applied magnetic flux density")
            plt.grid(True)
            plt.show()

            # Plot the effective core permeability vs applied magnetic field
            plt.figure()
            plt.plot(self.results['B'], self.results['mu_effs'], 'bo')
            plt.xlabel("Applied magnetic flux density magnitude [T]")
            plt.ylabel("Effective permeability")
            plt.title("Effective permeability vs applied magnetic flux density")
            plt.grid(True)
            plt.show()
        else:
            print("Nothing to plot, need to run simulation first.")


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

