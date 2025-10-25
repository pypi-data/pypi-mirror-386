# Forest Light Environmental Simulator (FLiES) Radiative Transfer Model Artificial Neural Network (ANN) Implementation in Python

This package is an artificial neural network emulator for the Forest Light Environmental Simulator (FLiES) model using keras and tensorflow in Python. This model is used to estimate solar radiation for the Breathing Earth Systems Simulator (BESS) model used to estimate evapotranspiration (ET) and gross primary productivity (GPP) for the ECOsystem Spaceborne Thermal Radiometer Experiment on Space Station (ECOSTRESS) and Surface Biology and Geology (SBG) thermal remote sensing missions.

## Contributors

[Gregory H. Halverson](https://github.com/gregory-halverson-jpl) (they/them)<br>
[gregory.h.halverson@jpl.nasa.gov](mailto:gregory.h.halverson@jpl.nasa.gov)<br>
Lead developer<br>
NASA Jet Propulsion Laboratory 329G

Hideki Kobayashi (he/him)<br>
FLiES algorithm inventor<br>
Japan Agency for Marine-Earth Science and Technology

## Installation

```
pip install FLiESANN
```

## Usage

```
from FLiESANN import FLiESANN
```

## References

If you use the **Forest Light Environmental Simulator (FLiES)** model in your work, please cite the following references:

1. Kobayashi, H., & Iwabuchi, H. (2008). *A coupled 1-D atmospheric and 3-D canopy radiative transfer model for canopy reflectance, light environment, and photosynthesis simulation in a heterogeneous landscape*. **Remote Sensing of Environment**, 112(1), 173-185.  
   [https://doi.org/10.1016/j.rse.2007.04.010](https://doi.org/10.1016/j.rse.2007.04.010)

2. Kobayashi, H., Ryu, Y., & Baldocchi, D. D. (2012). *A framework for estimating vertical profiles of canopy reflectance, light environment, and photosynthesis in discontinuous canopies*. **Agricultural and Forest Meteorology**, 150(5), 601-619.  
   [https://doi.org/10.1016/j.agrformet.2010.12.001](https://doi.org/10.1016/j.agrformet.2010.12.001)
