'''
(c) 2023 Twente Medical Systems International B.V., Oldenzaal The Netherlands

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
 * @file ForceFeedbackChart.py 
 * @brief 
 * ForceFeedbackChart object
 */


'''
import numpy as np
import colorsys

import pyqtgraph as pg
from PySide2 import QtCore

from TMSiFrontend.chart import Chart

class OnlineEMGChart(Chart):
    """Signal chart object
    """
    def __init__(self, plotter_chart):
        """Initialize the Signal chart

        :param plotter_chart: widget where the chart is going to lay.
        :type plotter_chart: QWidget
        """
        super().__init__(plotter_chart)
        self._curves = []
        self._plot_offset = 3
        self._default_window_size = 10
        self._plotter_chart.window.disableAutoRange()
        self._time_marker = None
        
    def initUI(self):
        """Initialize UI
        """
        # Set view settings
        self._plotter_chart.setBackground((255, 255, 255, 200))  
        self._plotter_chart.window = self._plotter_chart.addPlot()
        self._plotter_chart.window.showGrid(x = True, y = True, alpha = 0.5)
        self._plotter_chart.window.setLabel('bottom', 'Time', units='sec')
        self._plotter_chart.window.getViewBox().invertY(True)
        self._plotter_chart.window.setEnabled(False)
        self.set_time_range(1)

    def delete_time_marker(self):
        if self._time_marker:
            self._time_marker.clear()
            self._time_marker = None

    def set_time_min_max(self, x_min, x_max):
        """Set time range

        :param time_value: size of time window
        :type time_value: float
        """
        self._plotter_chart.window.setXRange(x_min, x_max, padding = 0)
    
    def set_time_range(self, time_value):
        """Set time range

        :param time_value: size of time window
        :type time_value: float
        """
        self._time_range = time_value
        self._plotter_chart.window.setXRange(-0.02*self._time_range, 1.03*self._time_range, padding = 0)
    
    def setup_signals(self, n_signals, colors = None):
        """Setup the signals

        :param n_signals: number of curves
        :type n_signals: int
        :param colors: colors of the signals, defaults to None
        :type colors: rgb tuple, optional
        """
        if hasattr(self, "_curves"):
            for c in range(len(self._curves)):
                self._curves[c].clear()
        self._curves = []
        color = self.generate_rainbow_colors(n_signals-2)
        for i in range(n_signals):
            if i == 0:
                c = pg.PlotCurveItem()
                c.setPen(color = (20,20,20), cosmetic = True, joinStyle = QtCore.Qt.MiterJoin, width = 3)
                self._plotter_chart.window.addItem(c)
                c.setPos(0,0*self._plot_offset)
                self._curves.append(c)
            elif i ==1:
                c = pg.PlotCurveItem()
                c.setPen(color = (252,  76, 2), cosmetic = True, joinStyle = QtCore.Qt.MiterJoin, width = 3)
                self._plotter_chart.window.addItem(c)
                c.setPos(0,0*self._plot_offset)
                self._curves.append(c) 
            else:
                c = pg.PlotCurveItem()
                c.setPen(color = color[i-2], cosmetic = True, joinStyle = QtCore.Qt.MiterJoin, width = 2)
                self._plotter_chart.window.addItem(c)
                c.setPos(0,(i-1)*self._plot_offset) # Disabled to get all the lines on the same height
                self._curves.append(c)
        self._plotter_chart.window.setYRange(-1.5, self._plot_offset * (n_signals-1) - 2 + 0.5, padding = 0)
    
    def generate_rainbow_colors(self, n_signals):
        """generate rainbow colors for the motor units

        :param n_signals: number of found motor units
        :type n_signals: int
        """
        # Initialize an empty list for colors
        colors = []
        # Iterate over the number of signals and evenly distribute hues across the color spectrum
        for i in range(n_signals):
            # Calculate the hue value by dividing the range of hues (0 to 1) equally among signals
            hue = i / float(n_signals)
            # Convert HSV to RGB
            rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            # Scale RGB values to 0-255 and round to integers
            colors.append((int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)))  
        return colors

    def update_chart(self, signals, time_span = None):
        """update chart

        :param signals: data to plot
        :type signals: list[list]
        :param time_span: time axis value, defaults to None
        :type time_span: list, optional
        """
        
        if len(self._curves) != len(signals):
            self.setup_signals(len(signals), (20,20,20))
        if len(signals) < 1:
            return
        if time_span is None:
            time_span = np.linspace(0, self._time_range, len(signals[0]))
        self._draw_signals(time_span[:len(signals[0])], signals)


    def update_time_marker(self, time_value):
        """Update time marker

        :param time_value: position of the marker
        :type time_value: float
        """
        if self._time_marker is None:
            self._time_marker = pg.PlotCurveItem()
            self._time_marker.setPen(color = "red", cosmetic = True, joinStyle = QtCore.Qt.MiterJoin)
            self._plotter_chart.window.addItem(self._time_marker)
        self._time_marker.setData([time_value, time_value], self._plotter_chart.window.viewRange()[1], connect="finite")
    
    def update_time_ticks(self, start_time, end_time):
        """Update ticks of the time axis

        :param start_time: initial tick position
        :type start_time: float
        :param end_time: final tick position
        :type end_time: float
        """
        tick_list_time = [[]]
        step_time = (end_time-start_time) / 5.0
        tick_list_time[0].append((0, "{:.2f}".format(start_time)))
        for i in range(1,5):
            tick_list_time[0].append((i * step_time, "{:.2f}".format(i * step_time + start_time)))
        tick_list_time[0].append((self._time_range, "{:.2f}".format(end_time)))
        self._plotter_chart.window.getAxis('bottom').setTicks(tick_list_time)

    def update_y_ticks(self, list_names, list_offsets, list_scales, list_units):
        """Update left axis ticks

        :param list_names: channel names
        :type list_names: list[str]
        :param list_offsets: offsets
        :type list_offsets: list[float]
        :param list_scales: scales
        :type list_scales: list[float]
        """
        # Displays values of the channel[-1] 
        if len(list_names) == 0: # Check if the list of names is empty. If the list is empty, set ticks for default values
            tick_list_left = [[]]
            tick_list_left[0].append(
                (0, "{}{:10.2f} {}".format('No Channels Selected', 0, 'a.u.')))
            tick_list_left[0].append(
                (-1, "{:10.2f} {}".format(-10, 'a.u.')))
            tick_list_left[0].append(
                (1, "{:10.2f} {}".format(10, 'a.u.')))
            self._plotter_chart.window.getAxis('left').setTicks(tick_list_left)
        else: # If the list of names is not empty, set ticks based on the values of last channel in the list.
            tick_list_left = [[]]
            for i in range(len(list_names)):
                if i == 0 or i == 1:
                    tick_list_left[0].append(
                        (0, "{}{:10.2f} {}".format(list_names[1], list_offsets[1], list_units[1])))
                    tick_list_left[0].append(
                        (-1, "{:10.2f} {}".format(list_offsets[1] + list_scales[1], list_units[1])))
                    tick_list_left[0].append(
                        (1, "{:10.2f} {}".format(list_offsets[1] - list_scales[1], list_units[1])))
                else:
                    tick_list_left[0].append(
                    ((i-1) * 3, "{}{:10.2f} {}".format(list_names[i], list_offsets[i], list_units[i])))
                    tick_list_left[0].append(
                    ((i-1) * 3 - 1, "{:10.2f} {}".format(list_offsets[i] + list_scales[i], list_units[i])))
                    tick_list_left[0].append(
                    ((i-1) * 3 + 1, "{:10.2f} {}".format(list_offsets[i] - list_scales[i], list_units[i])))
                self._plotter_chart.window.getAxis('left').setTicks(tick_list_left)


        
    def _draw_signals(self, x_values, y_values):
        for i in range(len(y_values)):
            self._curves[i].setData(
                x_values, y_values[i], connect="finite")

    