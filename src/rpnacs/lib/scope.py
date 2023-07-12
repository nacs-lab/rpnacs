import time
from . import utils
import numpy as np

class Scope:
    def __init__(self, rp):
        # rp is a redpitaya_scpi object defined in the file redpitaya_scpi.py file. It will handle all of the communication with the RedPitaya
        self.rp = rp

        # one time initiated variables, that is a property of the rp itself
        self.sampling_rate = 125e6 # Hard coded for now. Units of samples/second

        # trigger cache
        self.trig_cache = 'ACQ:TRIG NOW'

    ## Higher Level API
    def set_trigger(self, source, edge, level, delay=0):
        # set trigger source and edge type
        # returns None if inputs are incorrect
        if edge != 'PE' and edge != 'NE':
            return None
        self.set_trig_lev(level)
        self.set_trig_delay(delay)
        ret = self.set_trig_source(source, edge)
        self.trig_cache = ret
        return

    def set_time_res(self, res):
        # set decimation based on desired time resolution.
        # Time resolution specified in seconds.
        err_flag, buf_size = self.get_buf_size()
        # Time resolution is decimation / sampling_rate, so decimation is reslution * sampling_rate
        min_sampling_rate = 1/self.sampling_rate
        if res <= min_sampling_rate:
            dec = 1
        else:
            dec = res * self.sampling_rate
            # Now, we shift it to a power of 2.
            dec = 2**(np.floor(np.log2(dec))) # use floor to ensure resolution is better than the user specified one.
        self.set_dec(dec)
        err_flag, res = self.get_dec()
        return res / self.sampling_rate

    def set_time_total(self, total):
        # set decimation based on total time desired.
        # Total time specified in seconds.
        err_flag, buf_size = self.get_buf_size()
        max_dec = 2**16
        max_time = buf_size / self.sampling_rate * max_dec
        if total > max_time:
            dec = 2**16
        else:
            dec = total * self.sampling_rate / buf_size
            dec = 2**(np.ceil(np.log2(dec)))
        self.set_dec(dec)
        err_flag, res = self.get_dec()
        return buf_size / self.sampling_rate * res

    def get_time_points(self):
        err_flag, buf_size = self.get_buf_size()
        err_flag, dec = self.get_dec()
        t_tot = (buf_size - 1) / self.sampling_rate * dec
        ts = np.linspace(0, t_tot, buf_size)
        return ts

    def acquire_trace(self, timeout=60, holdoff = 0.005):
        # Acquires a trace and waits based on the decimation and the length of the acquired data
        # Returns the times as well based on the set decimation
        self.start_acq()
        self.rp.tx_txt(self.trig_cache)
        # wait for trigger with specified timeout
        start_time = time.time()
        cur_time = time.time()
        while cur_time - start_time < timeout:
            err_flag, stat = self.get_trig_status()
            if stat == 'TD':
                self.stop_acq()
                break
            time.sleep(holdoff) # holdoff before asking again
            cur_time = time.time()
        # get time points, at the moment t = 0 is the beginning of buffer which may not be the trigger location!
        ts = self.get_time_points()

        err_flag, ch1 = self.read_all_samples(1)
        err_flag, ch2 = self.read_all_samples(2)

        return ts, ch1, ch2

    ## Lower Level API
    # Acquisition related commands
    def start_acq(self):
        self.rp.tx_txt('ACQ:START')
        return

    def stop_acq(self):
        self.rp.tx_txt('ACQ:STOP')
        return

    def reset_acq(self):
        self.rp.tx_txt('ACQ:RST')
        return

    # Decimation related commands
    def get_dec(self):
        self.rp.tx_txt('ACQ:DEC?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, int(val)

    def set_dec(self, val):
        # Returns ERR! on error
        # Therefore, I will not error check and rely on a good caller or for the caller to check
        self.rp.tx_txt('ACQ:DEC ' + str(int(val)))
        return

    def get_avg(self):
        # Returns whether we are averaging over the time interval for decimation > 1
        self.rp.tx_txt('ACQ:AVG?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, val

    def set_avg(self, val):
        # Set whether we are averaging over the time interval or not for decimation. Can use either ON or OFF.
        self.rp.tx_txt('ACQ:AVG ' + str(val))
        return

    # Trigger related commands
    def set_trig_source(self, source, edge):
        # Source options:
        # -1: disabled
        # 0: now
        # 1: phys chn 1
        # 2: phys chn 2
        # 3: ext
        # 4: awg
        # Edge options: 'PE' or 'NE'
        source = int(source)
        if source == -1:
            ret_string = 'ACQ:TRIG DISABLED'
            self.rp.tx_txt(ret_string)
        elif source == 0:
            ret_string = 'ACQ:TRIG NOW'
            self.rp.tx_txt(ret_string)
        elif source == 1 or source == 2:
            ret_string = 'ACQ:TRIG CH' + str(source) + '_' + edge
            self.rp.tx_txt(ret_string)
        elif source == 3:
            ret_string = 'ACQ:TRIG EXT_' + edge
            self.rp.tx_txt(ret_string)
        elif source == 4:
            ret_string = 'ACQ:TRIG AWG_' + edge
            self.rp.tx_txt(ret_string)
        else:
            # default now trigger
            ret_string = 'ACQ:TRIG NOW'
            self.rp.tx_txt(ret_string)
        return ret_string

    def get_trig_status(self):
        self.rp.tx_txt('ACQ:TRIG:STAT?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, val

    def get_trig_delay(self):
        # Get trig delay in samples
        self.rp.tx_txt('ACQ:TRIG:DLY?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, int(val)

    def set_trig_delay(self, val):
        # Set trig delay in samples
        self.rp.tx_txt('ACQ:TRIG:DLY ' + str(int(val)))
        return

    def get_trig_delay_ns(self):
        # Get trig delay in ns
        self.rp.tx_txt('ACQ:TRIG:DLY:NS?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, int(val)

    def set_trig_delay_ns(self, val):
        # Set trig delay in ns
        self.rp.tx_txt('ACQ:TRIG:DLY:NS ' + str(int(val)))
        return

    def get_trig_hyst(self):
        # Get trigger hysteresis value in volts
        self.rp.tx_txt('ACQ:TRIG:HYST?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, float(val)

    def set_trig_hyst(self, val):
        # Set trigger hysteresis value in volts
        self.rp.tx_txt('ACQ:TRIG:HYST ' + str(val))
        return

    def get_trig_lev(self):
        # Get trigger level in volts
        self.rp.tx_txt('ACQ:TRIG:LEV?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, float(val)

    def set_trig_lev(self, val):
        # Set trigger level in volts
        self.rp.tx_txt('ACQ:TRIG:LEV ' + str(val))
        return

    # Data acquisition commands
    def get_data_units(self):
        # Get units in which data is returned
        self.rp.tx_txt('ACQ:DATA:UNITS?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, val

    def set_data_units(self, val):
        # Set units in which data is returned. Choose either RAW or VOLTS
        self.rp.tx_txt('ACQ:DATA:UNITS ' + str(val))
        return

    def set_data_format(self, val):
        # Set format of data. Choose either BIN or ASCII.
        self.rp.tx_txt('ACQ:DATA:FORMAT ' + str(val))
        return

    def read_samples_start_end(self, source, start, end):
        # Read samples from source, from start to end pos
        self.rp.tx_txt('ACQ:SOUR' + str(int(source)) + ':DATA:STA:END? ' + str(int(start)) + ',' + str(int(end)))
        datastr = self.rp.rx_txt()
        datastr = datastr.strip('{}\n\r').replace("  ", "").split(',')
        data = list(map(float, datastr))
        return data

    def read_samples_from(self, source, start, nsamples):
        # Read samples from source, nsamples starting from start
        self.rp.tx_txt('ACQ:SOUR' + str(int(source)) + ':DATA:STA:N? ' + str(int(start)) + ',' + str(int(nsamples)))
        err_flag, datastr = utils.rm_err(self.rp.rx_txt())
        datastr = datastr.strip('{}\n\r').replace("  ", "").split(',')
        data = list(map(float, datastr))
        return err_flag, data

    def read_all_samples(self, source):
        # Read full buffer
        self.rp.tx_txt('ACQ:SOUR' + str(int(source)) + ':DATA?')
        err_flag, datastr = utils.rm_err(self.rp.rx_txt())
        datastr = datastr.strip('{}\n\r').replace("  ", "").split(',')
        data = list(map(float, datastr))
        return err_flag, data

    def read_samples_from_trig(self, source, nsamples):
        # Read nsamples from trigger delay
        self.rp.tx_txt('ACQ:SOUR' + str(int(source)) + ':DATA:OLD:N? ' + str(int(nsamples)))
        err_flag, datastr = utils.rm_err(self.rp.rx_txt())
        datastr = datastr.strip('{}\n\r').replace("  ", "").split(',')
        data = list(map(float, datastr))
        return err_flag, data

    def read_samples_before_trig(self, source, nsamples):
        # Read nsamples before trigger delay
        self.rp.tx_txt('ACQ:SOUR' + str(int(source)) + ':DATA:LAT:N? ' + str(int(nsamples)))
        err_flag, datastr = utils.rm_err(self.rp.rx_txt())
        datastr = datastr.strip('{}\n\r').replace("  ", "").split(',')
        data = list(map(float, datastr))
        return err_flag, data

    def get_buf_size(self):
        # Get size of buffer
        self.rp.tx_txt('ACQ:BUF:SIZE?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, int(val)

    # Others
    def get_source_gain(self, source):
        # Get source gain, either LV or HV corresponding to jumper on red pitaya
        self.rp.tx_txt('ACQ:SOUR' + str(int(source)) + ':GAIN?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, val

    def set_source_gain(self, source, val):
        # Set source gain, either LV or HV corresponding to jumper on red pitaya
        self.rp.tx_txt('ACQ:SOUR' + str(int(source)) + ':GAIN ' + str(val))
        return
