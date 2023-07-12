from rpnacs.lib import DIOController
from rpnacs.lib import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import time

# Ugh, this is kind of strange.
# working configuration. Set trigger type after setting level.
# Then start acquisition once, and can constantly acquire without resetting trigger.
# Don't call start acquisition twice. lol

rp = scpi.scpi('192.168.0.200')
sc = DIOController.DIOController(rp)



while True:
    sc.set_led(0, 1)
    sc.set_led(2, 1)
    sc.set_led(4, 1)
    sc.set_led(6, 1)
    sc.set_led(1, 0)
    sc.set_led(3, 0)
    sc.set_led(5, 0)
    sc.set_led(7, 0)
    time.sleep(1)
    sc.set_led(0, 0)
    sc.set_led(2, 0)
    sc.set_led(4, 0)
    sc.set_led(6, 0)
    sc.set_led(1, 1)
    sc.set_led(3, 1)
    sc.set_led(5, 1)
    sc.set_led(7, 1)
    time.sleep(1)
