GeolAttitude
============
(c) 2026 Alessandro Frigeri - Italian National Institute for Astrophysics (INAF)

**GeolAttitude** is a QGIS plugin for estimating the orientation of geological planes in GIS picked 3D points.  The plug-in solves the three point problem within a GIS environment, where the user typically pick points over imagery while recording elevations from a DTM.

Background
----------

This plug-in comes from an appendix of an old PhD Thesis.  Originally a GRASS GIS script, it has been converted to QGIS. 

The development is being done within the scientific activities related to the ESA ExoMars rover mission to Mars, planneto to launch in 2028. 

With this plug-in you can estimate geologic attitude (dip, dip direction, strike) of planar feature out of your GIS data. 

Main Features
--------------

* Interactive picking: user can add or remove picked points interactively
* User-selectable fitting algorithms:
  - Least Squares plane fitting
  - PCA/SVD plane fitting
  - RANSAC robust plane fitting
* Uncertainty analysis
  - Residual statistics 
  - Outlier detection
  - dip and dip-direction uncertainty estimation via bootstrap numerical method
* Automatic 3D point layer generation

Contents
--------

.. toctree::
   :maxdepth: 2

   introduction
   installation
   quickstart
   algorithms
   bootstrap
   api
   changelog
