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
 * @file ${example_changing_configuration.py} 
 * @brief This example shows how to change the device sampling configuration. 
 * The example shows how to change the sampling frequency, disable the 
 * live-impedance measurement and set an impedance limit for the headcap 
 * indicator.
 * 
 */


'''


import sys
from os.path import join, dirname, realpath
Example_dir = dirname(realpath(__file__)) # directory of this file
modules_dir = join(Example_dir, '..') # directory with all modules
measurements_dir = join(Example_dir, '../measurements') # directory with all measurements
sys.path.append(modules_dir)

from TMSiSDK.tmsi_sdk import TMSiSDK, DeviceType, DeviceInterfaceType, DeviceState
from TMSiSDK.device import ApexEnums
from TMSiSDK.tmsi_errors.error import TMSiError


try:
    # Execute a device discovery. This returns a list of device-objects for every discovered device.
    TMSiSDK().discover(DeviceType.apex, DeviceInterfaceType.usb)
    discoveryList = TMSiSDK().get_device_list(DeviceType.apex)

    if (len(discoveryList) > 0):
        # Get the handle to the first discovered device.
        dev = discoveryList[0]
        
        # Open a connection to APEX
        dev.open()
    
        # Change the device configuration:
        # Change Sampling frequency to either 1000 Hz or 1024 Hz: 
        #   * Use 'Binary' for 1024 Hz
        #   * Use 'Decimal' for 1000 Hz
        # Disable live impedance measurement
        # Set impedance warning level (kOhms)
        dev.set_device_sampling_config(sampling_frequency = ApexEnums.ApexBaseSampleRate.Binary,
                                       live_impedance = ApexEnums.ApexLiveImpedance.Off,
                                       impedance_limit = 20)
        
        # Close the connection to the device
        dev.close()
        
except TMSiError as e:
    print(e)
        
finally:
    if 'dev' in locals():
        # Close the connection to the device when the device is opened
        if dev.get_device_state() == DeviceState.connected:
            dev.close()