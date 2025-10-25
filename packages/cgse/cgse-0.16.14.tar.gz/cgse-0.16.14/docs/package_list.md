# Packages in the CGSE

The CGSE is a monorepo and consists of numerous packages. Each of these packages are individually installable from 
PyPI. We maintain a list here with all the packages in the monorepo.

| Package                 | Description                                            | 
|-------------------------|--------------------------------------------------------|
| `cgse-common`           | The common code used by all other packages             |
| `cgse-core`             | The core services                                      |
| `cgse-coordinates`      | Coordinate reference Frames                            |
| `cgse-gui`              | GUI components and styles (PyQt5)                      |
| `cgse-tools`            | Plugin that adds functions to the `cgse` command       |
| `symetrie-hexapod`      | Device drivers for the Symétrie Hexapods               |
| `keithley-tempcontrol`  | Device driver for the Keithley temperature controller  |
| `lakeshore-tempcontrol` | Device driver for the LakeShore temperature controller |
| `plato-fits`            | FITS driver with PLATO specific format                 |
| `plato-hdf5`            | HDF5 driver with PLATO specific format                 |
| `plato-spw`             | SpaceWire driver with PATO specific packets            | 

The following is a non-exhaustive list of known external packages that work well with the CGSE 
in terms of commanding and monitoring.

| Package       | Description                                                                                                           |
|---------------|-----------------------------------------------------------------------------------------------------------------------|
| `cgse-dummy`  | Provides a dummy device driver to demonstrate plugins, commands and how to develop an external package for the CGSE.  |
