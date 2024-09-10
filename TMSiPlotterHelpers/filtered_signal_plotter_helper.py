'''
(c) 2023,2024 Twente Medical Systems International B.V., Oldenzaal The Netherlands

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
 * @file ${filtered_signal_plotter_helper.py}
 * @brief This file shows how to make a filtered plotter from the normal signal plotter.
 * The plotter itself is just a plotter that plots the data it recieves and does not have to be changed, 
 * instead the acquisition/plotter helper and the consumer thread have to be changed. These two classes 
 * are update in this file.
 * More information about how to make your own plotters can be found in the documentation.
 *
 */
'''

# Import relevant toolboxes and classes 
from scipy import signal
import numpy as np

from TMSiBackend.data_consumer.consumer_thread import ConsumerThread
from TMSiBackend.data_consumer.consumer import Consumer
from TMSiBackend.buffer import Buffer
from TMSiBackend.data_monitor.monitor import Monitor

from TMSiSDK.tmsi_utilities.support_functions import array_to_matrix as Reshape
from TMSiSDK.tmsi_sdk import ChannelType

from .signal_plotter_helper import SignalPlotterHelper
from .real_time_signal_plotter import RealTimeSignalPlotter


class FilteredSignalPlotterHelper(SignalPlotterHelper):
    def __init__(self, device, grid_type = None, hpf = 0, lpf = 0, order = 1):
        # call super of SignalPlotterHelper
        if device.get_device_type() == "APEX":
            super(SignalPlotterHelper, self).__init__(device = device,
                                                  monitor_class = Monitor, 
                                                  consumer_thread_class = FilteredConsumerThreadApex)
        else:    
            super(SignalPlotterHelper, self).__init__(device = device,
                                                  monitor_class = Monitor, 
                                                  consumer_thread_class = FilteredConsumerThread)
        self.main_plotter = RealTimeSignalPlotter()
        self._current_window_size = self.main_plotter.window_size   
        
        self.grid_type = grid_type
        self.hpf = hpf
        self.lpf = lpf
        self.order = order
    
    def initialize(self):
        super().initialize()
        self.n_unfiltered_channels = 0
        for ch in self.channels:
            if ch.get_channel_type() != ChannelType.UNI and ch.get_channel_type() != ChannelType.BIP:
                self.n_unfiltered_channels +=1

    def start(self):
        self.consumer = Consumer()
        self.consumer_thread = self.consumer_thread_class(
            consumer_reading_queue=self.consumer.reading_queue,
            sample_rate=self.device.get_device_sampling_frequency(), 
            n_unfiltered = self.n_unfiltered_channels
        )
        # Initialize filter
        self.consumer_thread.initialize_filter(hpf = self.hpf, lpf = self.lpf, order = self.order)
        self.consumer.open(
            server = self.device,
            reading_queue_id = self.device.get_id(),
            consumer_thread=self.consumer_thread)
        # Start measurement
        self.device.start_measurement(self.measurement_type)
        self.monitor = self.monitor_class(monitor_function = self.monitor_function, callback=self.callback, on_error=self.on_error)
        self.monitor.start()

    def monitor_function(self):
        reading = {}
        reading["status"] = 200
        reading["buffer"] = self.consumer_thread.filtered_buffer.copy()
        if self.device.get_device_type() == "APEX":
            reading["live_impedances"] = self.consumer_thread.cycling_impedance
        return reading

class FilteredConsumerThread(ConsumerThread):
    def __init__(self, consumer_reading_queue, sample_rate, n_unfiltered = 2):
        super().__init__(consumer_reading_queue, sample_rate)
        self.filtered_buffer = Buffer(sample_rate * 10)
        self.n_unfiltered = n_unfiltered
    
    def initialize_filter(self, hpf = 0, lpf = 0, order = 1):
        """Initialize the filter to be applied.

        :param hpf: high pass frequency, defaults to 0
        :type hpf: int, optional
        :param lpf: low pass frequency, defaults to 0
        :type lpf: int, optional
        :param order: order of the filter, defaults to 1
        :type order: int, optional
        """
        if hpf > 0 and lpf > 0:
            if hpf > lpf:
                self._sos = signal.butter(
                    order, [lpf, hpf], 'bandstop', fs=self.sample_rate, output='sos')
            else:
                self._sos = signal.butter(
                    order, [hpf, lpf], 'bandpass', fs=self.sample_rate, output='sos')     
        elif hpf > 0:
            self._sos = signal.butter(
                order,
                hpf,
                'highpass',
                fs=self.sample_rate,
                output='sos')
        elif lpf > 0:
            self._sos = signal.butter(
                order,
                lpf,
                'lowpass',
                fs=self.sample_rate,
                output='sos')
        else:
            self._sos = None

    def process(self, sample_data):
        reshaped = np.array(Reshape(sample_data.samples, sample_data.num_samples_per_sample_set))
        # Update original buffer
        self.original_buffer.append(reshaped)
        # Do not filter if no filter is present
        if not hasattr(self, "_sos") or self._sos is None:
            self.filtered_buffer.append(reshaped)
            return None
        # Construct initial conditions
        if not hasattr(self, "_z_sos"):
            self._z_sos = signal.sosfilt_zi(self._sos)
            self._z_sos1 = np.repeat(
                self._z_sos[:, np.newaxis, :], np.shape(reshaped)[0], axis=1)
        filtered, self._z_sos1 = self.__filter(reshaped)
        # Do not filter last n_unfiltered channels (f.e. STATUS and COUNTER)
        filtered[-self.n_unfiltered:] = reshaped[-self.n_unfiltered:]
        self.filtered_buffer.append(filtered)

    def __filter(self, reshaped):
        filtered, z_sos1 = signal.sosfilt(
                self._sos, reshaped, zi=self._z_sos1)
        return filtered, z_sos1

class FilteredConsumerThreadApex(FilteredConsumerThread):
    def __init__(self, consumer_reading_queue, sample_rate, n_unfiltered = 2):
        super().__init__(consumer_reading_queue = consumer_reading_queue, 
                         sample_rate = sample_rate, 
                         n_unfiltered = n_unfiltered)
        self.cycling_impedance = dict()

    def process(self, sample_data):
        super().process(sample_data)
        reshaped = np.array(Reshape(sample_data.samples, sample_data.num_samples_per_sample_set))
        self.collect_cycling_impedances(reshaped=reshaped)

    def collect_cycling_impedances(self, reshaped):
        for idx in range(len(reshaped[-5,:])):
                index = int(reshaped[-5,idx])+1
                if index in self.cycling_impedance:
                    self.cycling_impedance[index]["Re"] = reshaped[-4,idx]
                    self.cycling_impedance[index]["Im"] = reshaped[-3,idx]
                else:
                    self.cycling_impedance[index] = dict()
                    self.cycling_impedance[index]["Re"] = reshaped[-4,idx]
                    self.cycling_impedance[index]["Im"] = reshaped[-3,idx]
