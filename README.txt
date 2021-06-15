In order to run the program, open a command prompt running on a python 3.7 environment and type "python visualization.py elevationData.tif marsTexture.jpg"
The two files should be in the same directory as the python source.

There are two boolean variables near the top of the file which can be edited using a text editor / IDE:

heightMapping - when set to True, the program will create a visualization of mars with a heightmap with warped surface 
		with a height scale slider and water level slider.
	      - when set to False, the program will create a visualization of mars with contour lines shown through tubes
		with a tube radius slider and water level slider.
writeFile - when set to True, will write the sphere dataset into a file called "mars.vtk" which can be viewed in paraview.
	    Any existing mars.vtk will be overwritten.
	  - when set to False, the sphere dataset will not be written to a file.

