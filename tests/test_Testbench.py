from pywinding import Testbench, Sensor, Timer, cleanup
from matplotlib import pyplot as plt
import numpy as np
import logging
import matplotlib.pyplot as plt

try:
    import scienceplots
    plt.style.use(['science', 'ieee'])
except:
    logging.info("Science plots unavailable")

def main():
    ## USER: Define sensor specifications
    # Typical NDI sensor specs for 610099 sensor
    name='NDI_610099'
    length_sensor = 7.5
    sensor_OD = 0.5
    sensor_ID = 0.09
    length_core = 9
    core_OD = sensor_ID
    core_ID = 0
    wire_diameter = 0.025
    wire_diameter_copper = 0.025 # Diameter of the copper only
    packing_factor = 0.9
    core_material = 'Hiperco-50'

    ## USER: Define the Flux density range for testing
    B_start = 1e-9
    B_end = 100e-6
    f_test = 1000
    num_points = 10

    ## Define a sensor to be simulated in FEMM
    sensor = Sensor(length_sensor,sensor_ID,sensor_OD, length_core,core_ID,core_OD,wire_diameter,packing_factor,core_material,name)

    with Timer("Timing sweep"):
        ## Run the simulation
        print(f'GENERATING FEMM SWEEP FROM {B_start*1e6} uT to {B_end*1e6} uT over {num_points} points at {f_test} Hz\n\n')
        Bs = np.linspace(B_start,B_end,num_points)
        tb = Testbench()
        result = tb.simulate(sensor,Bs,f_test)
        plt.plot(result['B'], result['V'])
        plt.show()
        print(f"Mean sensitivity: {result['sensitivity_mean']}")
        print(f"μ_core: {result['mu_eff_mean']}")

    cleanup()

if __name__ == "__main__":
    main()