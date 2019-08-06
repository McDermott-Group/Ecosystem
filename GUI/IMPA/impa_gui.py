import sys
from PyQt4 import QtGui
from functools import partial

import labrad
from labrad.units import V, GHz, dBm

VOLTAGE_INCREMENT_STRING_TO_FLOAT = {'1 mV': 1e-3, '10 mV': 1e-2,
                                     '100 mV': 1e-1, '1 V': 1e0}

POWER_INCREMENT_STRING_TO_FLOAT = {'0.1 dBm': 1e-1, '0.2 dBm': 2e-1,
                                   '0.5 dBm': 5e-1, '1.0 dBm': 1e0,
                                   '10.0 dBm': 1e1}

FREQUENCY_INCREMENT_STRING_TO_FLOAT = {'1 MHz': 1e-3, '10 MHz': 1e-2,
                                   '100 MHz': 1e-1, '1 GHz': 1e0}


class IMPA_GUI(QtGui.QWidget):

    def __init__(self):
        super(IMPA_GUI, self).__init__()
        self.setWindowTitle('IMPA GUI')
        self.setWindowIcon(QtGui.QIcon('impa.png'))
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(10)
        self.cxn = labrad.connect()
        self.sim928 = self.cxn.sim928_test
        self.selected_sim_rack = None
        self.selected_sim_slot = None

        self.rf_generator = self.cxn.gpib_rf_generators
        self.selected_rf_generator = None
        self.initialize_rf_generator_selections()
        self.initialize_sim_rack_selections()
        self.setLayout(self.grid)
        self.show()

    def initialize_sim_rack_selections(self): # make all sim related stuff into class
        available_sim_racks = self.sim928.list_devices()
        self.sim_rack_selection_title = QtGui.QLabel('SIM900 Mainframe:')
        self.sim_rack_selection = QtGui.QComboBox()
        self.sim_rack_selection.addItem("Please Select a Mainframe")
        for ii in range(0, len(available_sim_racks)):
            self.sim_rack_selection.addItem(available_sim_racks[ii][1])
        if len(available_sim_racks) == 0:
            self.sim_rack_selection.removeItem(0)
            self.sim_rack_selection.addItem("No SIM900 Mainframes Were Detected")
            self.sim_rack_selection.setEnabled(False)
            self.sim_rack_selection_title.setEnabled(False)
        self.grid.addWidget(self.sim_rack_selection_title, 1, 1)
        self.grid.addWidget(self.sim_rack_selection, 2, 1)
        self.sim_rack_selection.activated[str].connect(self.select_sim_900_mainframe)

        self.sim_slot_selection_title = QtGui.QLabel('Select a SIM928:')
        self.sim_slot_selection = QtGui.QComboBox()
        self.sim_slot_selection.addItem("First Select a SIM 900 Mainframe")
        self.sim_slot_selection_title.setEnabled(False)
        self.sim_slot_selection.setEnabled(False)
        self.grid.addWidget(self.sim_slot_selection_title, 3, 1)
        self.grid.addWidget(self.sim_slot_selection, 4, 1)

        self.voltage_spinbox = QtGui.QDoubleSpinBox()
        self.voltage_spinbox_title = QtGui.QLabel('Voltage (V):')
        self.voltage_spinbox.setRange(-2., 2.)
        self.voltage_spinbox.setValue(0.0)
        self.voltage_spinbox.setDecimals(3)
        self.voltage_spinbox.setSingleStep(0.001)
        self.voltage_spinbox.valueChanged.connect(partial(call_labrad_setting,
                                                          self.sim928.set_voltage, V))

        self.voltage_increment_title = QtGui.QLabel('Voltage Increment:')
        self.voltage_increment = QtGui.QComboBox()
        self.voltage_increment.addItem("1 mV")
        self.voltage_increment.addItem("10 mV")
        self.voltage_increment.addItem("100 mV")
        self.voltage_increment.addItem("1 V")
        self.voltage_increment.activated[str].connect(partial(increment_updater, self.voltage_spinbox,
                                                              VOLTAGE_INCREMENT_STRING_TO_FLOAT))
        self.grid.addWidget(self.voltage_increment_title, 5, 1)
        self.grid.addWidget(self.voltage_increment, 6, 1)

        self.voltage_increment_title.setEnabled(False)
        self.voltage_increment.setEnabled(False)
        self.voltage_spinbox.setEnabled(False)
        self.voltage_spinbox_title.setEnabled(False)

        self.grid.addWidget(self.voltage_spinbox_title, 7, 1)
        self.grid.addWidget(self.voltage_spinbox, 8, 1)

    def initialize_rf_generator_selections(self):  # make all rf generator related stuff into class
        available_rf_generators = self.rf_generator.list_devices()
        self.rf_generator_selection_title = QtGui.QLabel('RF Generator:')
        self.rf_generator_selection = QtGui.QComboBox()
        self.rf_generator_selection.addItem("Please Select an RF Generator")
        for ii in range(0, len(available_rf_generators)):
            self.rf_generator_selection.addItem(available_rf_generators[ii][1])
        if len(available_rf_generators) == 0:
            self.rf_generator_selection.addItem("No RF Generators Were Detected")
        self.grid.addWidget(self.rf_generator_selection_title, 1, 2)
        self.grid.addWidget(self.rf_generator_selection, 2, 2)
        self.rf_generator_selection.activated[str].connect(self.select_rf_generator)

        self.rf_generator_power_increment_title = QtGui.QLabel('Power Increment:')
        self.rf_generator_power_increment_title.setEnabled(False)
        self.rf_generator_power_increment = QtGui.QComboBox()
        self.rf_generator_power_increment.addItem("0.1 dBm")
        self.rf_generator_power_increment.addItem("0.2 dBm")
        self.rf_generator_power_increment.addItem("0.5 dBm")
        self.rf_generator_power_increment.addItem("1.0 dBm")
        self.rf_generator_power_increment.addItem("10.0 dBm")

        self.rf_generator_power_increment.setEnabled(False)

        self.rf_generator_frequency_increment_title = QtGui.QLabel('Frequency Increment:')
        self.rf_generator_frequency_increment_title.setEnabled(False)
        self.rf_generator_frequency_increment = QtGui.QComboBox()
        self.rf_generator_frequency_increment.addItem("1 MHz")
        self.rf_generator_frequency_increment.addItem("10 MHz")
        self.rf_generator_frequency_increment.addItem("100 MHz")
        self.rf_generator_frequency_increment.addItem("1 GHz")

        self.rf_generator_frequency_increment.setEnabled(False)

        self.frequency_spinbox = QtGui.QDoubleSpinBox()
        self.frequency_spinbox_title = QtGui.QLabel('Frequency (GHz):')
        self.frequency_spinbox_title.setEnabled(False)
        self.frequency_spinbox.setRange(2., 14.)
        self.frequency_spinbox.setValue(4.0)
        self.frequency_spinbox.setDecimals(3)
        self.frequency_spinbox.setSingleStep(0.001)
        self.frequency_spinbox.valueChanged.connect(partial(call_labrad_setting,
                                                            self.rf_generator.frequency, GHz))
        self.frequency_spinbox.setEnabled(False)

        self.power_spinbox = QtGui.QDoubleSpinBox()
        self.power_spinbox_title = QtGui.QLabel('Power (dBm):')
        self.power_spinbox_title.setEnabled(False)
        self.power_spinbox.setRange(-80, 0.)
        self.power_spinbox.setValue(-20.0)
        self.power_spinbox.setDecimals(2)
        self.power_spinbox.setSingleStep(0.1)
        self.power_spinbox.valueChanged.connect(partial(call_labrad_setting,
                                                        self.rf_generator.power, dBm))
        self.power_spinbox.setEnabled(False)

        self.rf_generator_power_increment.activated[str].connect(partial(increment_updater, self.power_spinbox,
                                                                 POWER_INCREMENT_STRING_TO_FLOAT))

        self.rf_generator_frequency_increment.activated[str].connect(partial(increment_updater, self.frequency_spinbox,
                                                                     FREQUENCY_INCREMENT_STRING_TO_FLOAT))

        self.grid.addWidget(self.rf_generator_power_increment_title, 5, 2)
        self.grid.addWidget(self.rf_generator_power_increment, 6, 2)
        self.grid.addWidget(self.power_spinbox_title, 7, 2)
        self.grid.addWidget(self.power_spinbox, 8, 2)

        self.grid.addWidget(self.rf_generator_frequency_increment_title, 5, 3)
        self.grid.addWidget(self.rf_generator_frequency_increment, 6, 3)
        self.grid.addWidget(self.frequency_spinbox_title, 7, 3)
        self.grid.addWidget(self.frequency_spinbox, 8, 3)

    def select_rf_generator(self, selection):
        selection = str(selection)
        if selection != "Please Select an RF Generator" and selection != self.selected_rf_generator:
            if self.selected_rf_generator is None:
                self.rf_generator_selection.removeItem(0)
            self.selected_rf_generator = selection
            self.rf_generator.select_device(selection)
            current_frequency = self.rf_generator.frequency()['GHz']
            current_power = self.rf_generator.power()['dBm']
            self.frequency_spinbox.setValue(current_frequency)
            self.rf_generator_power_increment_title.setEnabled(True)
            self.rf_generator_power_increment.setEnabled(True)

            self.frequency_spinbox_title.setEnabled(True)
            self.frequency_spinbox.setEnabled(True)

            self.power_spinbox_title.setEnabled(True)
            self.power_spinbox.setEnabled(True)
            self.power_spinbox.setValue(current_power)

            self.frequency_spinbox_title.setEnabled(True)
            self.rf_generator_frequency_increment_title.setEnabled(True)
            self.rf_generator_frequency_increment.setEnabled(True)

    def select_sim_900_mainframe(self, selection):
        selection = str(selection)
        if selection != "Please Select a Mainframe" and selection != self.selected_sim_rack:
            if self.selected_sim_rack is None:
                self.sim_rack_selection.removeItem(0)
            self.selected_sim_rack = selection
            self.sim928.select_device(selection)
            self.sim_slot_selection_title.setEnabled(True)
            self.sim_slot_selection.setEnabled(True)
            self.sim_slot_selection.removeItem(0)
            self.sim_slot_selection.addItem("Please Select a Slot Number")
            for ii in range(1, 9):
                source_found = self.sim928.find_source(ii)
                if source_found:
                    self.sim_slot_selection.addItem("Slot #" + str(ii))
            if self.selected_sim_slot is None:
                self.sim_slot_selection.activated[str].connect(self.select_sim_928_slot)

    def select_sim_928_slot(self, selection):
        selection = str(selection)
        if selection != "Please Select a Slot Number" and selection != self.selected_sim_slot:
            if self.selected_sim_slot is None:
                self.sim_slot_selection.removeItem(0)
            slot_number = int(selection[-1])
            self.sim928.select_source(slot_number)
            self.selected_sim_slot = selection

            current_voltage = self.sim928.get_voltage()['V']
            self.voltage_spinbox.setValue(current_voltage)

            self.voltage_increment_title.setEnabled(True)
            self.voltage_increment.setEnabled(True)
            self.voltage_spinbox.setEnabled(True)
            self.voltage_spinbox_title.setEnabled(True)


def call_labrad_setting(labrad_setting, units, value): # all three set functions are essentially the same
    value = float(value)
    labrad_setting(value * units)

def increment_updater(spinbox, mapping, increment): # all three set functions are essentially the same
    increment = mapping[str(increment)]
    spinbox.setSingleStep(increment)

def main():
    app = QtGui.QApplication(sys.argv)
    ex = IMPA_GUI()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
