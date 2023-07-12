from rpnacs.lib import scope, FuncGenerator
from rpnacs.lib import redpitaya_scpi as scpi
import matplotlib.pyplot as plt

rp = scpi.scpi('192.168.0.200')
#sc = scope.Scope(rp)

#fgen = FuncGenerator.FuncGenerator(rp)
#fgen.set_amp(2, 0.3)
rp.tx_txt('SOUR1:FREQ:FIX 50')
#reply = rp.rx_txt()
#print(reply)
#err, val = fgen.get_amp(2)
#print(str(val))
