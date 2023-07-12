from lib import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import time

rp = scpi.scpi('192.168.0.200')

rp.tx_txt('ACQ:RST')
rp.tx_txt('ACQ:DATA:FORMAT ASCII')
rp.tx_txt('ACQ:DATA:UNITS VOLTS')

rp.tx_txt('ACQ:DEC 1')
rp.tx_txt('ACQ:TRIG:LEV 0.5')
rp.tx_txt('ACQ:TRIG:DLY 0')

rp.tx_txt('ACQ:START')
rp.tx_txt('ACQ:TRIG CH1_PE')

print('Waiting for trigger')
while 1:
    rp.tx_txt('ACQ:TRIG:STAT?')
    if rp.rx_txt() == 'TD':
        break

time.sleep(1)
print('Getting data from source 1')
rp.tx_txt('ACQ:SOUR1:DATA?')
buff_string = rp.rx_txt()
buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
buff = list(map(float, buff_string))

print('Getting data from source 2')
rp.tx_txt('ACQ:SOUR2:DATA?')
buff_string = rp.rx_txt()
buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
buff2 = list(map(float, buff_string))

rp.tx_txt('ACQ:BUF:SIZE?')
print(rp.rx_txt())

rp.tx_txt('*IDN?')
print(rp.rx_txt())

rp.tx_txt('SYST:VERS?')
print(rp.rx_txt())

plt.plot(buff, 'r')
plt.plot(buff2, 'g')
plt.ylabel('Voltage')
plt.show()
