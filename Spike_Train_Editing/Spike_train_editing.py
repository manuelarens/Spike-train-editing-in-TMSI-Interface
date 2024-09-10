'''
(c) 2022-2024 Twente Medical Systems International B.V., Oldenzaal The Netherlands

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

#######  #     #   #####   #
   #     ##   ##  #        
   #     # # # #  #        #
   #     #  #  #   #####   #
   #     #     #        #  #
   #     #     #        #  #
   #     #     #  #####    #

/**
 * @file ${example_EMG_workflow.py} 
 * @brief This example shows the functionality of the impedance plotter and an
 * HD-EMG heatmap. The user can disable channels based on measured impedances.
 * The heatmap displays the RMS value per channel, combined with linear 
 * interpolation to fill the space between channels.
 *
 */


'''

import sys
from os.path import join, dirname, realpath
Example_dir = dirname(realpath(__file__)) # directory of this file
modules_dir = join(Example_dir, '..') # directory with all modules
measurements_dir = join(Example_dir, '../measurements') # directory with all measurements
configs_dir = join(Example_dir, '../TMSiSDK\\tmsi_resources') # directory with configurations
sys.path.append(modules_dir)
import time

from PySide2.QtWidgets import *

from TMSiFileFormats.file_writer import FileWriter, FileFormat

from TMSiSDK.tmsi_sdk import TMSiSDK, DeviceType, DeviceInterfaceType, DeviceState
from TMSiSDK.tmsi_errors.error import TMSiError

from TMSiGui.gui import Gui
from TMSiPlotterHelpers.impedance_plotter_helper import ImpedancePlotterHelper
from TMSiPlotterHelpers.heatmap_plotter_helper import HeatmapPlotterHelper

from .offline_EMG import EMG_Decomposition
from .force_feedback_plotter_helper import ForceFeedbackPlotterHelper

try:
    # Execute a device discovery. This returns a list of device-objects for every discovered device.
    TMSiSDK().discover(dev_type = DeviceType.saga, dr_interface = DeviceInterfaceType.docked, ds_interface = DeviceInterfaceType.usb)
    discoveryList = TMSiSDK().get_device_list(DeviceType.saga)

    if (len(discoveryList) > 0):
        # Get the handle to the first discovered device and open the connection.
        for i,_ in enumerate(discoveryList):
            dev = discoveryList[i]
            if dev.get_dr_interface() == DeviceInterfaceType.docked:
                # Open the connection to SAGA
                dev.open()
                break
        
        grid_type = '4-8-L'
        # options:'4-8-L', '6-11-L', '6-11-S', '8-8-L', '8-8-S', '6-11-L-1', '6-11-L-2', '6-11-S-1', '6-11-S-2', '8-8-L-1', '8-8-L-2', '8-8-S-1', '8-8-S-2'

        Force_channel = 'AUX 1-2'
        
        # Load the HD-EMG channel set and configuration
        print("load HD-EMG config")
        if dev.get_num_channels()<64:
            dev.import_configuration(join(configs_dir, "saga32_config_textile_grid_" + grid_type + ".xml"))
        else:
            dev.import_configuration(join(configs_dir, "saga64_config_textile_grid_" + grid_type + ".xml"))
        
        # Check if there is already a plotter application in existence
        app = QApplication.instance()
        
        # Initialise the plotter application if there is no other plotter application
        if not app:
            app = QApplication(sys.argv)
        
        # Initialise the helper
        plotter_helper = ImpedancePlotterHelper(device=dev,
                                                 grid_type=grid_type, 
                                                 file_storage = join(measurements_dir,"example_EMG_workflow"))
        # Define the GUI object and show it 
        gui = Gui(plotter_helper = plotter_helper)
         # Enter the event loop
        app.exec_()
        
        # Pause for a while to properly close the GUI after completion
        print('\n Wait for a bit while we close the plot... \n')
        time.sleep(1)

        ##################################################################################################################################
        
        # Ask for desired file format
        file_format=input("Which file format do you want to use? (Options: xdf or poly5)\n")
        
        # Initialise the desired file-writer class and state its file path
       # if file_format.lower()=='poly5':
        #    file_writer = FileWriter(FileFormat.poly5, join(measurements_dir,"example_EMG_workflow.poly5"))
        #elif file_format.lower()=='xdf':
        #    file_writer = FileWriter(FileFormat.xdf, join(measurements_dir,"example_EMG_workflow.xdf"), add_ch_locs=False)
        #else:
        #    print('File format not supported. File is saved to XDF-format.')
        plotter_helper = ForceFeedbackPlotterHelper(device=dev, meas_type= 1, force_channel=Force_channel, 
                                                        filename = join(measurements_dir,"MVC_measurement+ForceProfile"), hpf=20, lpf=500, order=2,
                                                        file_type='xdf')

        EMG_reject = []
        print('START OFFLINE DECOMPOSITION')
        offline_decomp = EMG_Decomposition(rejected_chan=EMG_reject)
        offline_decomp.run(grid_name=grid_type)
        filepath_decomp = offline_decomp.emg_obj.file_path_json
        print("OFFLINE DECOMPOSITION DONE")
        
        # Close the connection to the SAGA device
        dev.close()
    
except TMSiError as e:
    print(e)
    
        
finally:
    if 'dev' in locals():
        # Close the connection to the device when the device is opened
        if dev.get_device_state() == DeviceState.connected:
            dev.close()