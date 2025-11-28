from pywinding import Testbench_B_Sweep, Coil

# PyWinding MUST be called from either a function or from the Python interpreter. Do NOT call PyWinding from a script.
# Otherwise the multiprocess code will fail and strange errors will occur.
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

    # This is a default testcoil design.
    # A 1 meter diameter air core coil consisting of 1 turn.
    # Expected Results for the testcoil based on theoretical for Sensitivity, Inductance and Resistance:
    #   - Sensitivity should align to theoretical prediction of S = 4.9348 [volts per tesla per hertz]
    #   - Effective relative permeability = 1
    #   - Inductance = 4.15 [microhenries]
    #   - Resistance = 0.0689 [ohms]
    name = 'test_microcoil'
    ls = 6.5                    # ls  : length of the sensor coil
    ods = 0.5                   # ods : outer diameter of the sensor coil
    ids = 0.09                  # ids : inner diameter of the sensor coil
    lc = 9                      # lc  : length of the magnetic core
    odc = ids                   # idc : inner diameter of the magnetic core (typically 0)
    idc = 0                     # odc :  outer diameter of the magnetic core (typically same as ids)
    odw = 0.025                 # odw : outer diameter of the wire used to wind the sensor including insulation, as this is used to calculate the number of turns.
    odwc= 0.025                 # odwc : outer diameter of the copper wire cross section only
    pf = 1                      # pf  : The packing factor
    ma = 'Hiperco-50'           # ma  : The core material (must be defined within the FEMM program)
    force_n = False             # Set to False if you wish the program to deduce the number of turns based on the provded coil geometry

    # Define the Flux density range for testing
    B_start = 1e-6          # The flux density to begin the sweep
    B_end = 5e-6            # The flux density to end the sweep
    f_test = 1000           # The excitation frequency at which to perform analysis.
    num_points = 10          # The number of points to use for the sweep

    # Create an instance of the coil to be simulated based on the user-defined specifications above.
    testcoil = Coil(ls,ids,ods,lc,idc,odc,odw,pf,ma,name, odwc=odwc, explicit_n=force_n)

    # Create a testbench configured to perform a magnitude sweep.
    tb = Testbench_B_Sweep(f_test, B_start, B_end, num_points)

    # Call the testbench's simulate method to execute the sweep. The sweep is distributed across CPU cores.
    #  Set cleanup flag to true to remove .fem and .ans files
    results = tb.simulate(testcoil, clean_up_femm=True)

    # Print the key results to the console
    tb.print_results()

    # Plot the sensor response over the applied field
    tb.plot_results()

    # Save the resulting data to a .mat file for further analysis and plotting
    tb.save_results()



if __name__ == "__main__":
    main()