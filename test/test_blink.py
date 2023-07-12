import sys
import time
from lib import redpitaya_scpi as scpi

rp = scpi.scpi('192.168.0.200')

led = 0

print("Blinking LED")

period = 1 #seconds

while 1:
    time.sleep(period/2.0)
    rp.tx_txt('DIG:PIN LED0, 1')
    time.sleep(period/2.0)
    rp.tx_txt('DIG:PIN LED0, 0')
