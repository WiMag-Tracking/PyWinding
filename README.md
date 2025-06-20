# pywinding
 Automated winding design for micro coils based on [sensor-toolkit](https://github.com/AlexJaeger/sensor-toolkit)

## Introduction

This software toolkit attempts to simplify the design and development of induction coil sensors for use with electromagnetic tracking systems. The toolkit leverages the scriptable nature of the the Finite Element Method Magnetics software (https://www.femm.info/wiki/HomePage) to create a simplified design procedure for induction coils.

Given a set of coil geometry and material specifications the toolkit will:
1. Calculate the remaining mechanical parameters of the coil
2. Build the sensor geometry
3. Generate a list of FEMM simulation files containing the sensor within a Helmholtz coil array
4. Simulate the sensor's response to a user-defined sweep of magnetic flux densities
5. Simulate the electrical parameters of the sensor, Resistance (Ohms) and Inductance (Henries)
6. Print the results on-screen


## Required
Ensure FEMM 4.2 is installed on your system in the default installation directory `C:\femm42`.

Use `test_run_sweep.m` to run a the simulation.
Sensor parameters are specified and explained at top of file.

Use `remove_files.m` to remove all .fem and .ans files from the directory.


## Right to use
If you've been added to this repository feel free to use it in your research project. Do not redistribute this code unless the author gives permission to do so, as this work has not yet been published.
Simulations have been verified to be within 5-10% of the real-world measurements, however the author takes no responsibitlity for the accuracy of this simulation toolkit.
If the use of this toolkit contributes to a publication then please acknowledge the author by name in that publication.
