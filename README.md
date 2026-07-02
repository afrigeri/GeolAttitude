Dip Direction Sampler QGIS Plugin
===================================

**(c) 2026 - Alessandro Frigeri, Italian National Institute for Astrophysics (INAF)** 

Highly interactive least square plane fitting QGIS Plug-in for computation of dip and dip direction from Digital Elevation Models (DEMs).


__This is Free Open Source Software__ distributed under GPL 3.0 License.

What's Next
In your plugin directory, compile the resources file using pyrcc5 (simply run make if you have automake or use pb_tool) 
Test the generated sources using make test (or run tests from your IDE) 
Copy the entire directory containing your new plugin to the QGIS plugin directory (see Notes below) 
Test the plugin by enabling it in the QGIS plugin manager 
Customize it by editing the implementation file dip_direction_sampler.py 
Create your own custom icon, replacing the default icon.png 
Modify your user interface by opening dip_direction_sampler_dockwidget_base.ui in Qt Designer 
Notes: 
You can use the Makefile to compile and deploy when you make changes. This requires GNU make (gmake). The Makefile is ready to use, however you will have to edit it to add addional Python source files, dialogs, and translations. 
You can also use pb_tool to compile and deploy your plugin. Tweak the pb_tool.cfg file included with your plugin as you add files. Install pb_tool using pip or easy_install. See http://loc8.cc/pb_tool for more information. 
For information on writing PyQGIS code, see http://loc8.cc/pyqgis_resources for a list of resources. 
©2011-2018 GeoApt LLC - geoapt.com 
