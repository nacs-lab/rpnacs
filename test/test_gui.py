import sys
import numpy as np
import queue
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QPushButton, QLineEdit, QLabel, QSizePolicy, QComboBox, QCheckBox
from PyQt5.QtCore import QMutex, QObject, QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from rpnacs.lib import scope, FuncGenerator, DIOController
from rpnacs.lib import redpitaya_scpi as scpi
import time
import random
from enum import Enum

class MutexManager:
    def __init__(self, mutex):
        self.mutex = mutex

    def __enter__(self):
        self.mutex.lock()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.mutex.unlock()

class ScopeWorkerCmds(Enum):
    Kill = 0
    SetScopeTime = 1
    SetTrigger = 2
    SetTimeout = 3

class ScopeWorker(QThread):
    # signal when trace is acquired
    trace_acquired = pyqtSignal()
    # signal for when a cmd is acknowledged
    cmd_acknowledged = pyqtSignal(int)
    # signal when thread is killed
    finished = pyqtSignal()
    # trigger_timeout
    trigger_timeout = 1;

    def __init__(self, sc, shared_list, cmd_queue, cmd_mutex,  data, data_mutex):
        # sc is a two element list. First element is a Scope object (or None). Second element is a mutex
        # shared_list is how the outside communicates with the worker. It is read-only for the worker. Communicate out of worker using signals.
        # The first element determines whether traces should be acquired
        # cmd_queue is a queue of commands

        # data is a list of lists to share the times, and channels acquired by the scope
        # data_mutex controls access to ts, chn1, chn2
        self.sc = sc
        self.shared_list = shared_list
        self.cmd_queue = cmd_queue
        self.cmd_mutex = cmd_mutex
        self.data = data
        self.data_mutex = data_mutex
        super().__init__()

    def run(self):
        # list of cmd_queue commands
        # 0: stop and kill worker thread
        # 1: set time scale
        # 2: set trigger
        # 3: set timeout
        while True:
            try:
                with self.cmd_mutex:
                    cmd = self.cmd_queue.get(False) # non-blocking retrieval
            except queue.Empty:
                cmd = None
            if self.sc[0] is not None:
                # process cmds first and then acquire trace
                if cmd is None:
                    # No commands mean acquire traces if allowed.
                    if self.shared_list[0] == 1:
                        with self.sc[1]:
                            ts, ch1, ch2 = self.sc[0].acquire_trace(self.trigger_timeout,0)
                        with self.data_mutex:
                            self.data[0] = ts
                            self.data[1] = ch1
                            self.data[2] = ch2
                        self.trace_acquired.emit()
                else:
                    cmd_type = cmd[0]
                    # here process commands
                    if cmd_type == ScopeWorkerCmds.Kill:
                        break
                    elif cmd_type == ScopeWorkerCmds.SetScopeTime:
                        # set time command
                        with self.sc[1]:
                            self.sc[0].set_time_total(cmd[1])
                        self.cmd_acknowledged.emit(1)
                    elif cmd_type == ScopeWorkerCmds.SetTrigger:
                        with self.sc[1]:
                            self.sc[0].set_trigger(cmd[1], cmd[2], cmd[3])
                        self.cmd_acknowledged.emit(2)
                    elif cmd_type == ScopeWorkerCmds.SetTimeout:
                        self.trigger_timeout = cmd[1];
                        self.cmd_acknowledged.emit(3)
            # This sleep here prevents this thread from taking all the runtime.
            time.sleep(0.5)
        self.finished.emit()

class PlotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plot App")
        self.is_running = False

        # Create status label
        if random.random() < 0.05:
            default_status_label = "I love you!"
        else:
            default_status_label = "Hello [INSERT USER NAME]! Welcome to the Red Pitaya locking module"
        self.status_label = QLabel(default_status_label, self)


        # Create Red Pitaya related objects
        self.rp = None
        self.rp_mutex = MutexManager(QMutex())
        self.dio = None

        # Create Scope related objects
        self.sc = [None, self.rp_mutex]
        self.sc_data = [[], [], []]
        self.sc_data_mutex = MutexManager(QMutex())
        self.sc_shared_list = [0]
        self.sc_cmd_queue = queue.Queue()
        self.sc_cmd_mutex = MutexManager(QMutex())
        self.scope_worker = ScopeWorker(self.sc, self.sc_shared_list, self.sc_cmd_queue, self.sc_cmd_mutex, self.sc_data, self.sc_data_mutex)
        self.scope_worker.trace_acquired.connect(self.update_plot)
        self.scope_worker.cmd_acknowledged.connect(self.sc_cmd_acknowledged)
        self.scope_worker.start()

        # Create a Figure object and a plot for scope
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.line1, = self.ax.plot([0, 1], [0,0], label='Line 1')
        self.line2, = self.ax.plot([0, 1], [0,0], label ='Line 2')

        # Create buttons
        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_plot)
        self.start_button.setEnabled(True)
        self.stop_button = QPushButton("Stop", self)
        self.stop_button.clicked.connect(self.stop_plot)
        self.stop_button.setEnabled(False)
        self.clear_button = QPushButton("Clear", self)
        self.clear_button.clicked.connect(self.clear_plot)
        self.clear_button.setEnabled(False)

        # Create the IP address connection
        self.rp_ip_field = QLineEdit('192.168.0.200', self)
        self.rp_ip_label = QLabel('Red Pitaya IP Address', self)
        #self.rp_ip_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.rp_connect_button = QPushButton("Connect", self)
        self.rp_connect_button.clicked.connect(self.connect_rp)
        self.rp_connect_button.setEnabled(True)
        self.rp_disconnect_button = QPushButton("Disconnect", self)
        self.rp_disconnect_button.clicked.connect(self.disconnect_rp)
        self.rp_disconnect_button.setEnabled(False)

        # Create Scope settings
        self.sc_label = QLabel('SCOPE SETTINGS', self)
        self.sc_time_label = QLabel('Total Time (s): ', self)
        self.sc_time_field = QLineEdit('0.03', self)
        self.sc_time_button = QPushButton("Set", self)
        self.sc_time_button.clicked.connect(self.set_scope_time)
        self.sc_time_button.setEnabled(True)
        # Check trigger settings
        self.sc_trig_label = QLabel('Trigger Settings ', self)
        self.sc_trig_chn_label = QLabel('Channel', self)
        self.sc_trig_edge_label = QLabel('Edge', self)
        self.sc_trig_lev_label = QLabel('Level', self)
        self.sc_trig_chn = QComboBox(self)
        self.sc_trig_chn.addItem("1")
        self.sc_trig_chn.addItem("2")
        self.sc_trig_edge = QComboBox(self)
        self.sc_trig_edge.addItem("PE")
        self.sc_trig_edge.addItem("NE")
        self.sc_trig_lev = QLineEdit('0.3', self)
        self.sc_trig_set_button = QPushButton("Set", self)
        self.sc_trig_set_button.clicked.connect(self.set_sc_trigger)
        self.sc_trig_set_button.setEnabled(True)
        self.sc_trig_timeout_label = QLabel('Trigger Timeout (s) ', self)
        self.sc_trig_timeout = QLineEdit('1', self)
        self.sc_trig_timeout_button = QPushButton("Set", self)
        self.sc_trig_timeout_button.clicked.connect(self.set_sc_trig_timeout)
        self.sc_trig_timeout_button.setEnabled(True)

        # Create FuncGenerator Settings
        self.fg = None
        self.fg_label = QLabel('FUNCTION GENERATOR SETTINGS', self)
        self.fg_chn_label = QLabel('Func Generator Chn: ', self)
        self.fg_chn = QComboBox(self)
        self.fg_chn.addItem("1")
        self.fg_chn.addItem("2")
        self.fg_chn.currentIndexChanged.connect(self.refresh_fg_settings)
        self.fg_freq_label = QLabel('Frequency', self)
        self.fg_freq = QLineEdit('1', self)
        self.fg_freq_units = QComboBox(self)
        self.fg_freq_units.addItem("Hz")
        self.fg_freq_units.addItem("kHz")
        self.fg_freq_units.addItem("MHz")
        self.fg_freq_button = QPushButton("Set", self)
        self.fg_freq_button.clicked.connect(self.set_fg_freq)
        self.fg_freq_button.setEnabled(True)
        self.fg_amp_label = QLabel('Amplitude', self)
        self.fg_amp = QLineEdit('0.5', self)
        self.fg_amp_button = QPushButton("Set", self)
        self.fg_amp_button.clicked.connect(self.set_fg_amp)
        self.fg_amp_button.setEnabled(True)
        self.fg_amp_units = QLabel('Volts', self)
        self.fg_offset_label = QLabel('Offset', self)
        self.fg_offset = QLineEdit('0', self)
        self.fg_offset_button = QPushButton("Set", self)
        self.fg_offset_button.clicked.connect(self.set_fg_offset)
        self.fg_offset_button.setEnabled(True)
        self.fg_offset_units = QLabel('Volts', self)
        self.fg_phase_label = QLabel('Phase', self)
        self.fg_phase = QLineEdit('0', self)
        self.fg_phase_button = QPushButton("Set", self)
        self.fg_phase_button.clicked.connect(self.set_fg_phase)
        self.fg_phase_button.setEnabled(True)
        self.fg_phase_units = QLabel('Degrees', self)
        self.fg_wform_label = QLabel('Waveform', self)
        self.fg_wform = QComboBox(self)
        self.fg_wform.addItem("SINE")
        self.fg_wform.addItem("SQUARE")
        self.fg_wform.addItem("TRIANGLE")
        self.fg_wform.addItem("SAWU")
        self.fg_wform.addItem("SAWD")
        self.fg_wform.addItem("DC")
        self.fg_wform_button = QPushButton("Set", self)
        self.fg_wform_button.clicked.connect(self.set_fg_wform)
        self.fg_wform_button.setEnabled(True)
        self.fg_enable = QCheckBox("Enable", self)
        self.fg_enable.stateChanged.connect(self.set_fg_enable)
        self.fg_set_all_button = QPushButton("Set all", self)
        self.fg_set_all_button.clicked.connect(self.set_fg_all)
        self.fg_set_all_button.setEnabled(True)

        # Locking TTLs
        self.lock_ttl_label = QLabel('Locking TTL: ', self)
        self.lock_ttl_selector = QComboBox(self)
        self.lock_ttl_selector.addItem("0")
        self.lock_ttl_selector.addItem("1")
        self.lock_ttl_selector.addItem("2")
        self.lock_ttl_selector.addItem("3")
        self.lock_ttl_selector.addItem("4")
        self.lock_ttl_selector.addItem("5")
        self.lock_ttl_selector.addItem("6")
        self.lock_ttl_selector.addItem("7")
        self.lock_ttl_selector.activated.connect(self.select_ttl)
        self.lock_ttl_id = QLabel('DIO0_N', self)
        self.lock_ttl_value = QComboBox(self)
        self.lock_ttl_value.addItem("LOW")
        self.lock_ttl_value.addItem("HIGH")
        self.lock_ttl_value.activated.connect(self.set_ttl)
        self.lock_ttl_dir = QComboBox(self)
        self.lock_ttl_dir.addItem("OUT")
        self.lock_ttl_dir.addItem("IN")
        self.lock_ttl_dir.activated.connect(self.set_ttl_dir)

        # Set up the layout
        layout = QGridLayout()
        layout.addWidget(self.status_label,0,0,1,3)
        layout.addWidget(self.lock_ttl_label,0,3,1,1)
        layout.addWidget(self.lock_ttl_selector,0,4,1,1)
        layout.addWidget(self.lock_ttl_id,0,5,1,1)
        layout.addWidget(self.lock_ttl_value,0,6,1,1)
        layout.addWidget(self.lock_ttl_dir,0,7,1,1)
        layout.addWidget(self.canvas,1,0,12,3)
        layout.addWidget(self.start_button,13,0)
        layout.addWidget(self.stop_button,13,1)
        layout.addWidget(self.clear_button,13,2)
        layout.addWidget(self.rp_ip_field,2,3,1,4)
        layout.addWidget(self.rp_ip_label,1,3,1,4)
        layout.addWidget(self.rp_connect_button,2,7,1,1)
        layout.addWidget(self.rp_disconnect_button,1,7,1,1)
        # scope
        layout.addWidget(self.sc_label,3,3,1,5)
        layout.addWidget(self.sc_time_label,4,3,1,1)
        layout.addWidget(self.sc_time_field,4,4,1,3)
        layout.addWidget(self.sc_time_button,4,7,1,1)
        layout.addWidget(self.sc_trig_label,5,3,1,1)
        layout.addWidget(self.sc_trig_timeout_label,5,4,1,1)
        layout.addWidget(self.sc_trig_timeout,5,5,1,2)
        layout.addWidget(self.sc_trig_timeout_button,5,7,1,1)
        layout.addWidget(self.sc_trig_chn_label,6,3,1,1)
        layout.addWidget(self.sc_trig_edge_label,6,4,1,1)
        layout.addWidget(self.sc_trig_lev_label,6,5,1,1)
        layout.addWidget(self.sc_trig_chn,7,3,1,1)
        layout.addWidget(self.sc_trig_edge,7,4,1,1)
        layout.addWidget(self.sc_trig_lev,7,5,1,2)
        layout.addWidget(self.sc_trig_set_button,7,7,1,1)
        # fgen
        layout.addWidget(self.fg_label,8,3,1,4)
        layout.addWidget(self.fg_chn_label,9,3,1,1)
        layout.addWidget(self.fg_chn,9,4,1,1)
        layout.addWidget(self.fg_enable,9,5,1,1)
        layout.addWidget(self.fg_set_all_button,9,6,1,1)
        layout.addWidget(self.fg_wform_label,10,3,1,1)
        layout.addWidget(self.fg_wform,11,3,1,1)
        layout.addWidget(self.fg_wform_button,13,3,1,1)
        layout.addWidget(self.fg_freq_label,10,4,1,1)
        layout.addWidget(self.fg_freq,11,4,1,1)
        layout.addWidget(self.fg_freq_units,12,4,1,1)
        layout.addWidget(self.fg_freq_button,13,4,1,1)
        layout.addWidget(self.fg_amp_label,10,5,1,1)
        layout.addWidget(self.fg_amp,11,5,1,1)
        layout.addWidget(self.fg_amp_units,12,5,1,1)
        layout.addWidget(self.fg_amp_button,13,5,1,1)
        layout.addWidget(self.fg_offset_label,10,6,1,1)
        layout.addWidget(self.fg_offset,11,6,1,1)
        layout.addWidget(self.fg_offset_units,12,6,1,1)
        layout.addWidget(self.fg_offset_button,13,6,1,1)
        layout.addWidget(self.fg_phase_label,10,7,1,1)
        layout.addWidget(self.fg_phase,11,7,1,1)
        layout.addWidget(self.fg_phase_units,12,7,1,1)
        layout.addWidget(self.fg_phase_button,13,7,1,1)

        # Create a central widget to hold the layout
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def connect_rp(self):
        try:
            rp = scpi.scpi(self.rp_ip_field.text(), timeout=10, port=5000)
        except:
            self.status_label.setText("Connection to Red Pitaya failed")
            return
        self.status_label.setText("Connected to Red Pitaya!")
        self.rp = rp
        sc = scope.Scope(self.rp)
        self.sc[0] = sc
        self.fg = FuncGenerator.FuncGenerator(self.rp)
        self.dio = DIOController.DIOController(self.rp)
        self.rp_connect_button.setEnabled(False)
        self.rp_disconnect_button.setEnabled(True)
        # default parameters for scope.
        sc.reset_acq()
        sc.set_data_units('VOLTS')
        sc.set_data_format('ASCII')
        # trigger and time scale should be adjustable
        sc.set_trigger(1, 'PE', 0.3) # edge and level don't matter if it's just being triggered all the time
        sc.set_time_total(30e-3)
        sc.start_acq()

        # get func gen settings
        self.refresh_fg_settings(0)
        self.refresh_fg_settings(1)

        # get DIO settings for TTL0
        self.select_ttl(0)

    def disconnect_rp(self):
        # perform a reset essentially
        if self.rp is not None:
            self.sc[0] = None
            self.stop_plot()
            with self.rp_mutex:
                self.rp.close()
            self.rp = None
            self.fg = None
            self.dio = None
            self.rp_connect_button.setEnabled(True)
            self.rp_disconnect_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.start_button.setEnabled(True)
            self.status_label.setText("Red Pitaya disconnected!")

    def set_scope_time(self):
        if self.rp is not None:
            try:
                val = float(self.sc_time_field.text())
            except ValueError as err:
                self.status_label.setText("ERROR: Enter a number for the time!")
                return
            with self.sc_cmd_mutex:
                self.sc_cmd_queue.put([ScopeWorkerCmds.SetScopeTime, val])

    def set_sc_trigger(self):
        if self.rp is not None:
            chn = int(self.sc_trig_chn.currentText())
            edge = self.sc_trig_edge.currentText()
            try:
                lev = float(self.sc_trig_lev.text())
            except ValueError as err:
                self.status_label.setText("ERROR: Enter a number for the trigger level!")
                return
            with self.sc_cmd_mutex:
                self.sc_cmd_queue.put([ScopeWorkerCmds.SetTrigger, chn, edge, lev])

    def set_sc_trig_timeout(self):
        if self.rp is not None:
            try:
                val = float(self.sc_trig_timeout.text())
            except ValueError as err:
                self.status_label.setText("ERROR: Enter a number for the timeout!")
                return
            with self.sc_cmd_mutex:
                self.sc_cmd_queue.put([ScopeWorkerCmds.SetTimeout, val])

    def sc_cmd_acknowledged(self, cmd_type):
        if cmd_type == ScopeWorkerCmds.SetScopeTime:
            self.status_label.setText("Time scale of scope set!")
        elif cmd_type == ScopeWorkerCmds.SetTrigger:
            self.status_label.setText("Trigger setting set!")
        elif cmd_type == ScopeWorkerCmds.SetTimeout:
            self.status_label.setText("Trigger timeout set!")

    def start_plot(self):
        if self.rp is not None:
            self.sc_shared_list[0] = 1
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("Scope plot started!")

    def stop_plot(self):
        if self.rp is not None:
            self.sc_shared_list[0] = 0
            self.stop_button.setEnabled(False)
            self.start_button.setEnabled(True)
            self.status_label.setText("Scope plot stopped!")

    def clear_plot(self):
        return

    def update_plot(self):
        with self.sc_data_mutex:
            ts = self.sc_data[0]
            ch1 = self.sc_data[1]
            ch2 = self.sc_data[2]
        self.line1.set_data(ts, ch1)
        self.line2.set_data(ts, ch2)
        self.ax.relim()
        self.ax.autoscale_view()

        # Redraw the canvas
        self.canvas.draw_idle()

    # Function Generator functions
    def refresh_fg_settings(self, idx):
        if self.rp is not None:
            # This is zero indexed
            with self.rp_mutex:
                freq_err, freq = self.fg.get_freq(idx + 1)
                amp_err, amp = self.fg.get_amp(idx + 1)
                offset_err, offset = self.fg.get_offset(idx + 1)
                phase_err, phase = self.fg.get_phase(idx + 1)
                wform_err, wform = self.fg.get_waveform(idx + 1)
                enable_err, enable = self.fg.get_state(idx + 1)
            unit = self.fg_freq_units.currentIndex()
            freq = freq / 10**(unit * 3)
            self.fg_freq.setText(str(freq))
            self.fg_amp.setText(str(amp))
            self.fg_offset.setText(str(offset))
            self.fg_phase.setText(str(phase))
            if wform == "SINE":
                self.fg_wform.setCurrentIndex(0)
            elif wform == "SQUARE":
                self.fg_wform.setCurrentIndex(1)
            elif wform == "TRIANGLE":
                self.fg_wform.setCurrentIndex(2)
            elif wform == "SAWU":
                self.fg_wform.setCurrentIndex(3)
            elif wform == "SAWD":
                self.fg_wform.setCurrentIndex(4)
            elif wform == "DC":
                self.fg_wform.setCurrentIndex(5)
            if enable == "1":
                self.fg_enable.setCheckState(2)
            elif enable == "0":
                self.fg_enable.setCheckState(0)
            self.status_label.setText("Function Generator Chn " + str(idx + 1) + " Settings restored")
            #self.status_label.setText("Amp: " + str(amp))
        return

    def set_fg_freq(self):
        if self.rp is not None:
            val = int(float(self.fg_freq.text()))
            unit = self.fg_freq_units.currentIndex()
            val = val * 10**(unit * 3)
            if val >= 0 and val <= 62.5 * 10**6:
                chn_num = self.fg_chn.currentIndex() + 1
                with self.rp_mutex:
                    self.fg.set_freq(chn_num, val)
            else:
                self.status_label.setText("Please enter a frequency between 0 and 62.5 MHz")
                return
        return

    def set_fg_amp(self):
        if self.rp is not None:
            val = float(self.fg_amp.text())
            if val >= -1 and val <= 1:
                chn_num = self.fg_chn.currentIndex() + 1
                with self.rp_mutex:
                    self.fg.set_amp(chn_num, val)
                self.status_label.setText("Function Generator Amplitude set!")
            else:
                self.status_label.setText("Please enter a float value between -1 and 1")
                return
        return

    def set_fg_offset(self):
        if self.rp is not None:
            val = float(self.fg_offset.text())
            if val >= -1 and val <= 1:
                chn_num = self.fg_chn.currentIndex() + 1
                with self.rp_mutex:
                    self.fg.set_offset(chn_num, val)
                self.status_label.setText("Function Generator Offset set!")
            else:
                self.status_label.setText("Please enter a float value between -1 and 1")
                return
        return

    def set_fg_phase(self):
        if self.rp is not None:
            val = int(self.fg_phase.text())
            if val >= -360 and val <= 360:
                chn_num = self.fg_chn.currentIndex() + 1
                with self.rp_mutex:
                    self.fg.set_phase(chn_num, val)
                self.status_label.setText("Function Generator Phase set!")
            else:
                self.status_label.setText("Please enter a integer between -360 and 360")
                return
        return


    def set_fg_wform(self):
        if self.rp is not None:
            chn_num = self.fg_chn.currentIndex() + 1
            wform = self.fg_wform.currentText()
            with self.rp_mutex:
                self.fg.set_waveform(chn_num, wform)
            self.status_label.setText("Function Generator Waveform set!")
        return

    def set_fg_enable(self):
        if self.rp is not None:
            chn_num = self.fg_chn.currentIndex() + 1
            enabled = self.fg_enable.isChecked()
            if enabled:
                self.fg.enable_output(chn_num)
                self.status_label.setText("Channel " + str(chn_num) + " enabled")
            else:
                self.fg.disable_output(chn_num)
                self.status_label.setText("Channel " + str(chn_num) + " disabled")
        return

    def set_fg_all(self):
        if self.rp is not None:
            self.set_fg_wform()
            self.set_fg_freq()
            self.set_fg_amp()
            self.set_fg_offset()
            self.set_fg_phase()
            self.status_label.setText("All settings to function generator set!")
        return

    def select_ttl(self, idx):
        if self.rp is not None:
            with self.rp_mutex:
                err, state = self.dio.get_pin_state(idx, 'N')
                err_dir, direction = self.dio.get_pin_direction(idx, 'N')
            self.lock_ttl_id.setText('DIO' + str(idx) + '_N')
            self.lock_ttl_value.setCurrentIndex(state)
            if direction == "OUT":
                self.lock_ttl_dir.setCurrentIndex(0)
            elif direction == "IN":
                self.lock_ttl_dir.setCurrentIndex(1)
        return

    def set_ttl(self, idx):
        if self.rp is not None:
            chn = self.lock_ttl_selector.currentIndex()
            with self.rp_mutex:
                self.dio.set_pin_state(chn, idx, 'N')
            self.status_label.setText("TTL " + str(chn) + 'set!')
        return

    def set_ttl_dir(self, idx):
        if self.rp is not None:
            chn = self.lock_ttl_selector.currentIndex()
            direction = self.lock_ttl_dir.currentText()
            with self.rp_mutex:
                self.dio.set_pin_direction(chn, direction, 'N')
            self.status_label.setText("TTL" + str(chn) + 'set!')
        return

# Create the PyQt application
app = QApplication(sys.argv)

# Create the main window
window = PlotWindow()
window.show()

# Start the PyQt event loop
sys.exit(app.exec_())
