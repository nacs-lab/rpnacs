from rpnacs.lib import scope
from rpnacs.lib import redpitaya_scpi as scpi
import matplotlib.pyplot as plt


# Ugh, this is kind of strange.
# working configuration. Set trigger type after setting level.
# Then start acquisition once, and can constantly acquire without resetting trigger.
# Don't call start acquisition twice. lol

rp = scpi.scpi('192.168.0.200')
sc = scope.Scope(rp)

# Test functions
#rp.tx_txt('ACQ:DEC 5')
#print(rp.rx_txt())
#sc.set_dec(5)
#print(sc.get_dec())
sc.reset_acq()
sc.set_data_units('VOLTS')
sc.set_data_format('ASCII')
sc.set_trigger(0, 'PE', 0)
#res = sc.set_time_total(100e-6)
sc.set_dec(1)
sc.set_time_total(30e-3)
#err_flag, val = sc.get_dec()
#print(val)
#err_flag, val = sc.get_buf_size()
#print(val)
sc.start_acq()
ts, ch1, ch2 = sc.acquire_trace(1,0)

plt.plot(ts, ch1, 'r')
plt.plot(ts, ch2, 'g')
plt.ylabel('Voltage')
plt.show()

#sc.set_trigger(1, 'PE', 0.5)
#sc.stop_acq()
#sc.start_acq()
ts, ch1a, ch2a = sc.acquire_trace(1,0)

print(ch1 == ch1a)
print(ch2 == ch2a)

plt.plot(ts, ch1a, 'r')
plt.plot(ts, ch2a, 'g')
plt.ylabel('Voltage')
plt.show()

