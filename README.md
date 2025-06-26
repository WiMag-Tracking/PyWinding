[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15705727.svg)](https://doi.org/10.5281/zenodo.15705727)

<p align="center">
  <a>
    <img src="https://github.com/WiMag-Tracking/PyWinding/blob/main/docs/img/icon.png?raw=true" width="400">
  </a>

  <h3 align="center">PyWinding</h3>

  <p align="center">
    A simulation tool for the design and evaluation of induction coils
    <br>
    <a href="https://www.github.com/WiMag-Tracking/PyWinding/issues/new?template=bug.md">Report bug</a>
    ·
    <a href="https://www.github.com/WiMag-Tracking/PyWinding/issues/new?template=feature.md&labels=feature">Request feature</a>
  </p>
</p>

| **Parameter** | **Description**                 |
|--------------------|--------------------------------------|
| $D_o$              | Total diameter of the sensor         |
| $D_i$              | Outer diameter of sensor core only   |
| $d_o$              | Total diameter of magnet wire        |
| $d_i$              | Diameter of the magnetic wire copper |
| $l_w$              | Length of the winding                |
| $l_c$              | Length of the core                   |

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

Use `test_Testbench.py` to run a test simulation.
Sensor parameters are specified and explained at top of file.

## Right to use
If you've been added to this repository feel free to use it in your research project. Do not redistribute this code unless the author gives permission to do so, as this work has not yet been published.
Simulations have been verified to be within 5-10% of the real-world measurements, however the author takes no responsibitlity for the accuracy of this simulation toolkit.
If the use of this toolkit contributes to a publication then please acknowledge the author by name in that publication.