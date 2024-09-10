'''
(c) 2024 Twente Medical Systems International B.V., Oldenzaal The Netherlands

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
 * @file measurement_type.py
 * @brief Extension of TMSi MeasurementType
 *
 */


'''

from TMSiSDK.device.tmsi_device_enums import MeasurementType as TMSiMeasurementType

from .signal_measurement import SignalMeasurement as WaveXSignalMeasurement

class MeasurementType(TMSiMeasurementType):
    WAVEX_SIGNAL = WaveXSignalMeasurement