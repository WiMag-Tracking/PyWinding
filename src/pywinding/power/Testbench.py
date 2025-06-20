from ..Magneto import Magneto
import numpy as np
import os
import logging
import concurrent.futures
from tqdm import tqdm
from datetime import datetime
import multiprocessing as mp
from .Helmholtz import Helmholtz
import pickle
import copy
    
SIM_DEFAULTS = {
    'units'     :   'millimeters',  # units
    'symmetry'  :   'axi',          # symmetry
    'precision' :   1e-8,           # precision
    'ddimension':   0,              # depth dimension
    'ang_cons'  :   30              # angular constraint
}

AIR = ('Air', 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0)

path_prefix = 'temp/'

class Testbench():
    def __init__(self, freq=1e3, **kwargs):
        self.__simulator = Magneto()
        self.freq = freq
        self.__sim_kwargs = {**{'freq' : self.freq}, **{k : kwargs.get(k, v) for k,v in SIM_DEFAULTS.items()}}
        self.path = None
        if not os.path.isdir("temp"):
            os.mkdir("temp")

    @property
    def freq(self):
        return self._freq

    @freq.setter
    def freq(self, f):
        self._freq = f

    def __create_filename(self, sen, helm):
        sim_file_name = f"{sen.na}_{sen.ma}_sensor_{str(helm.B)}_T_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_{np.random.rand()}.fem"
        sim_file_name = sim_file_name.replace(" ", "")
        sim_file_name = sim_file_name.replace(":", "")

        return f"{path_prefix}{sim_file_name}"

    def simulate(self, sen, Bs=np.array([1e-6]), freq=1e3):
        
        self.freq = freq
        # build Helmholtz for given test flux density
        helm = Helmholtz( 100*sen.ls, Bs[0], self.freq, 5, 1 )

        # need to deep copy here instead of passing reference
        sensor_air  = copy.deepcopy(sen)
        sensor_core = copy.deepcopy(sen)
        
        sensor_air.ma = 'Air'
        sensor_core.ma = sen.ma
        
        self.__sim_objs = (sensor_air , helm)
        path_air =  self.__draw()
        self.__sim_objs = (sensor_core, helm)
        path_core = self.__draw()
        
        path_airs  = [path_air]
        path_cores = [path_core]
        
        #########################################################
        # WRITE SIMS
        if len(Bs) > 1:
            for sensor, path, paths in zip([sensor_air, sensor_core], [path_air, path_core], [path_airs, path_cores]):
                self.__simulator.openfemm(True)
                self.__simulator.opendocument(str(path))
                for j, B in enumerate(Bs[1:]):
                    helm = Helmholtz( 100*sensor.ls, B, self.freq, 5, 1 )
                    
                    self.__simulator.mi.modifycircprop('icoil_transmitter', 1, helm.i)
                    sim_file_name = self.__create_filename(sen, helm)
                    self.__simulator.mi.saveas(sim_file_name)
                    paths.append(str(sim_file_name))
                
                self.__simulator.closefemm()
        #########################################################
        # CREATE FUTURES
        with concurrent.futures.ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
            # A list to store futures for data parsing
            futures = []
            for path_air, path_core in tqdm(zip( path_airs, path_cores),desc="Sweeping B"):
                futures.append(executor.submit(run,  *[sensor_air,  path_air ]))
                futures.append(executor.submit(run,  *[sensor_core, path_core]))
            
            concurrent.futures.wait(futures)
        futures_air =  futures[0::2]
        futures_core = futures[1::2]
        #########################################################
        # PARSE
        B_air =  np.array([f.result()['B'] for f in futures_air])
        B_core = np.array([f.result()['B'] for f in futures_core])
        v_air =  np.array([f.result()['V'] for f in futures_air])
        v_core = np.array([f.result()['V'] for f in futures_core])

        sensitivity = v_core / (B_air * self.freq)
        mu_eff = B_core / B_air
        LR_PARAMS = self.__extract(path_air, path_core, self.freq, sen.odwc)

        result = {
            'V'                 : v_core,
            'B'                 : B_air,
            'sensitivities'     : sensitivity,
            'sensitivity_mean'  : np.mean(sensitivity),
            'sensitivity_std'   : np.std(sensitivity),
            'mu_effs'           : mu_eff,
            'mu_eff_mean'       : np.mean(mu_eff),
            'mu_eff_std'        : np.std(mu_eff),
            'path_air'          : path_airs,
            'path_core'         : path_cores
        }

        logging.info("COIL MAGNETIC PARAMETERS:\n")
        logging.info(f"Mean Sensitivity [Volts per (Tesla Hz)] = {result['sensitivity_mean']}, Standard Deviation = {result['sensitivity_std']}\n")
        logging.info(f"Effective permeability = {result['mu_eff_mean']}, Standard Deviation = {result['mu_eff_std']}\n\n")

        return result

    def __draw(self):

        self.__simulator.init(hide=False, **self.__sim_kwargs)

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
        self.__simulator.mi.addmaterial( *AIR )

        for obj in self.__sim_objs:
            self.__simulator.mi.addmaterial( * obj.material )

        for obj in self.__sim_objs:
            obj._properties( self.__simulator )
        
        self.__simulator.mi.zoomnatural()
        
        path = self.__create_filename( *self.__sim_objs )
        self.__simulator.mi.saveas( path )
        self.__simulator.closefemm()
        
        return path
    
    def __extract(self, path_air, path_core, f, odwc):
        parameters = {}
        for ma, path in zip( ['air', 'core'], [path_air, path_core]):
            self.__simulator.openfemm(False)
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

        logging.info("COIL ELECTRICAL PARAMETERS:\n")
        logging.info("Sensor Air:\n")
        logging.info(f"Resistance = {parameters['resistance_air']} [Ohms], Inductance = {parameters['inductance_air']} [Henries]\n\n")
        logging.info("Sensor Core:\n")
        logging.info(f"Resistance = {parameters['resistance_core']} [Ohms], Inductance = {parameters['inductance_core']} [Henries]\n\n")

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