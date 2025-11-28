# pywinding
 Automated winding design for micro coils based on [sensor-toolkit](https://github.com/AlexJaeger/sensor-toolkit)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15705727.svg)](https://doi.org/10.5281/zenodo.15705727)

## Overview

This software toolkit simplifies the design and simulation of induction microcoils. The toolkit leverages the PyFEMM interface of the Finite Element Method Magnetics software (https://www.femm.info/wiki/HomePage) to allow users to rapidly characterise the magnetic behaviour of induction microcoils containing permeable magnetic cores.

Given a set of user defined coil geometry and simulation parameters the toolkit will:
1. Calculate the remaining mechanical parameters of the coil
2. Build the sensor geometry
3. Generate a list of .fem simulation files for a sweep of magnetic flux densities
4. Simulate the sensor's response using all available CPU cores
5. Extract the electrical parameters of the sensor, Resistance (Ohms) and Inductance (Henries)
6. Print and plot the results on-screen
7. Save the results to a .mat file


## Installation

Ensure FEMM 4.2 (available at https://www.femm.info/wiki/HomePage) is installed on your system in the default installation directory `C:\femm42`.

Install the latest version of pywinding from Pypi with:
```python
python -m pip install pywinding
```

##  Usage (command-line)

The pywinding tool can be used directly from the command line interpreter. 

From the interpreter import the pywinding classes for defining the geometry of a coil and the testbench for which to evaluate the sensor:
```python
>>> from pywinding import Coil, Testbench_B_Sweep
```
Define the geometry of an induction microcoil. An example definition is given below
```python
>>> name = 'test_microcoil'
>>> ls = 6.5                    # ls  : length of the sensor coil
>>> ods = 0.5                   # ods : outer diameter of the sensor coil
>>> ids = 0.09                  # ids : inner diameter of the sensor coil
>>> lc = 9                      # lc  : length of the magnetic core
>>> odc = ids                   # idc : inner diameter of the magnetic core (typically 0)
>>> idc = 0                     # odc :  outer diameter of the magnetic core (typically same as ids)
>>> odw = 0.025                 # odw : outer diameter of the wire used to wind the sensor including insulation, as this is used to calculate the number of turns.
>>> odwc= 0.025                 # odwc : outer diameter of the copper wire cross section only
>>> pf = 1                      # pf  : The packing factor
>>> ma = 'Hiperco-50'           # ma  : The core material (must be defined within the FEMM program)
>>> force_n = False             # Set to False if you wish the program to deduce the number of turns based on the provded coil geometry

>>> testcoil = Coil(ls,ids,ods,lc,idc,odc,odw,pf,ma,name, odwc=odwc, explicit_n=force_n)
```
Create an instance of the simulation testbench specifying the test frequency, the range of magnetic flux densities (in tesla) and the number of simulation points within this range.
```python
>>> f_test = 1000    # The stimulus frequency for the simulation
>>> B_start = 1e-9   # The starting flux density (in tesla)
>>> B_end = 1e-6     # The ending flux density (in tesla)
>>> num_points = 10  # The number of simulation points to use in the sweep

>>> tb = Testbench_B_Sweep(f_test, B_start, B_end, num_points)
```
Run the simulation by passing the coil geometry to the testbench
```python
>>> results = tb.simulate(testcoil, clean_up_femm=False) # Specify the program not to delete the FEMM files ocne complete
```
Multiple instance of the FEMM tool should launch in the background

Once simulation is complete you can view the results to console and plot the response using:
```python
>>> tb.print_results()   # Print the coil parameters to the console
>>> tb.plot_results()    # Plot the coil response using matplotlib
```
The results can be saved to a ```.mat``` file using:
```python
>>> tb.save_results()
```

## Tests
The above usage example can be is available as a script in the ```tests``` folder


## Right to use
If you've been added to this repository feel free to use it in your research project. Simulations have been verified to be within 5-10% of the real-world measurements, however the author takes no responsibitlity for the accuracy of this simulation toolkit.
If the use of this toolkit contributes to a publication then please acknowledge the author by name in that publication.
