from pywinding import Testbench_B_Sweep, Coil, cleanup
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams['axes.formatter.useoffset'] = False

def main():
    """
        Define the parameters for coil, all dimensions in millimetres
        name: A string representing the name of the coil
        ls  : length of the sensor coil
        ids : inner diameter of the sensor coil
        ods : outer diameter of the sensor coil
        lc  : length of the magnetic core
        idc : inner diameter of the magnetic core (typically 0)
        odc :  outer diameter of the magnetic core (typically same as ids)
        odw : outer diameter of the wire used to wind the sensor including
        insulation, as this is used to calculate the number of turns.
        pf : packing factor (0.9 for circular wire)
        ma : string representing the material of the core
        explicit_n : if False, n is computed internally, if integer value is provided, it is used as the number of turns.
     """
    name = 'testcoil'
    ls = 6.5                # ls  : length of the sensor coil
    ods = 0.5               # ods : outer diameter of the sensor coil
    ids = 0.09              # ids : inner diameter of the sensor coil
    lc = 9                  # lc  : length of the magnetic core
    odc = ids               # idc : inner diameter of the magnetic core (typically 0)
    idc = 0                 # odc :  outer diameter of the magnetic core (typically same as ids)
    odw = 0.025             # odw : outer diameter of the wire used to wind the sensor including insulation, as this is used to calculate the number of turns.
    odwc= 0.025             # odwc : outer diameter of the copper wire cross section only
    pf = 1                  # pf  : The packing factor
    ma = 'Hiperco-50'       # ma  : The core material (must be defined within the FEMM program)
    force_n = False         # Set to False if you wish the program to deduce the number of turns based on the provded coil geometry

    ## Define the Flux density range for testing
    B_start = 1e-6          # The flux density to begin the sweep
    B_end = 3e-6            # The flux density to end the sweep
    f_test = 1000           # The excitation frequency at which to perform analysis.
    num_points = 50        # The number of points to use for the sweep

    # Create an instance of the coil to be simulated based on the user-defined specifications above.
    testcoil = Coil(ls,ids,ods,lc,idc,odc,odw,pf,ma,name, odwc=odwc, explicit_n=force_n)

    # Create a testbench configured to perform a magnitude sweep. Set cleanup flag to true to remove .fem and .ans files
    tb = Testbench_B_Sweep(f_test, B_start, B_end, num_points, True)


    ## Call the testbench's simulate method to execute the sweep. The sweep is distributed across CPU cores.
    result = tb.simulate(testcoil)
    # Save the resulting data to a .mat file for
    tb.save_result(result)



    """
    The results structure contains the following variables:
       result = {
                'Name'             - The name of the coil
                'V'                - An array of voltage magnitudes for each applied field in the sweep
                'B'                - An array of applied magnetic flux densities applied in the sweep
                'Rair'             - The resistance of the coil when an air core is used
                'Rcore'            - The resistance of the coil when the user defined core material is used
                'Lair'             - The inductance of the coil when an air core is used
                'Lcore'            - The inductance of the coil when the user defined core material is used
                'sensitivities'    - An array of coil sensitivities calculated for each applied field in the sweep
                'sensitivity_mean' - The mean sensitivity of the coil calculated by averaging the sensitivities array
                'sensitivity_std'  - The standard deviation of the sensitivity array
                'mu_effs'          - An array of the effective magnetic permeability of the user defined core relative to air
                'mu_eff_mean'      - 
                'mu_eff_std'       - 
                'path_air'         - 
                'path_core'        - 
            }
    
    """
    ## Plot the sensor response over the applied field
    plt.figure()
    plt.plot(result['B'], result['V'],'bo')
    plt.xlabel("Applied magnetic flux density magnitude [T]")
    plt.ylabel("Voltage amplitude [V]")
    plt.title("Sensor voltage vs applied magnetic flux density")
    left = result['B'][0]
    top = result['V'][-1]
    plt.text(left,top,"Mean Sensitivity [V/(T.Hz)] = " + '%.7f'%(result['sensitivity_mean']))
    plt.grid(True)
    #ax.get_yaxis().get_major_formatter().set_useOffset(False)
    plt.show()

    # Plot the sensor sensitivity [in V/(T.Hz)] vs. the applied magnetic field
    plt.figure()
    plt.plot(result['B'], result['sensitivities'],'bo')
    plt.xlabel("Applied magnetic flux density magnitude [T]")
    plt.ylabel("Coil sensitivity [V/(T.Hz)]")
    plt.title("Coil sensitivity vs applied magnetic flux density")
    plt.grid(True)
    plt.show()

    # Plot the effective core permeability vs applied magnetic field
    plt.figure()
    plt.plot(result['B'], result['mu_effs'],'bo')
    plt.xlabel("Applied magnetic flux density magnitude [T]")
    plt.ylabel("Effective permeability")
    plt.title("Effective permeability vs applied magnetic flux density")
    plt.grid(True)
    plt.show()

    # Print the key results to the console
    print(f"Mean sensitivity: {result['sensitivity_mean']}")
    print(f"μ_core: {result['mu_eff_mean']}")
    print(f"Resistance (air): {result['Rair']}")
    print(f"Resistance (core): {result['Rcore']}")
    print(f"Inductance (air): {result['Lair']}")
    print(f"Inductance (core): {result['Lcore']}")


if __name__ == "__main__":
    main()