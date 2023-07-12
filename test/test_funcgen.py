from rpnacs.lib import FuncGenerator
from rpnacs.lib import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import time

rp = scpi.scpi('192.168.0.200')
fgen = FuncGenerator.FuncGenerator(rp)

# set_output(self, chn, waveform, freq, amp, offset=0, phase=0):
fgen.set_output(1, 'TRIANGLE', 10e3, 0.5, 0.25, 0)
fgen.set_output(2, 'SQUARE', 1e3, 0.75)
fgen.enable_output(1)
fgen.enable_output(2)

time.sleep(20)

fgen.disable_output(1)
#fgen.disable_output(2)
