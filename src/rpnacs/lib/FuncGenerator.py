import time
from . import utils
import numpy as np

class FuncGenerator:
    def __init__(self, rp):
        # rp is a redpitaya_scpi object defined in the file redpitaya_scpi.py file. It will handle all of the communication with the RedPitaya
        self.rp = rp

    ## Higher level API
    def set_output(self, chn, waveform, freq, amp, offset=0, phase=0):
        # Set output channel chn to the waveform specified by waveform at the frequency and amplitude
        # Not error checking for now...
        self.set_waveform(chn, waveform)
        self.set_freq(chn, freq)
        self.set_amp(chn, amp)
        self.set_offset(chn, offset)
        self.set_phase(chn, phase)
        return

    def enable_output(self, chn):
        # enable outputs
        # if chn = 0, then enable all outputs at once.
        # if chn = 1,2 then just enable those channels
        if chn == 0:
            self.set_all_states('ON')
            self.trigger_all_now()
        else:
            self.set_state(chn, 'ON')
            self.trigger_chn_now(chn)
        return

    def disable_output(self, chn):
        # disable outputs
        # if chn = 0, disable all outputs at once.
        # if chn = 1,2 then just disable those channels
        if chn == 0:
            self.set_all_states('OFF')
        else:
            self.set_state(chn, 'OFF')
        return

    ## Lower level API
    def set_all_states(self, val):
        # set all states to either ON or OFF
        self.rp.tx_txt('OUTPUT:STATE ' + val)
        return

    def set_state(self, source, val):
        # set channel 1 or 2 to ON or OFF
        self.rp.tx_txt('OUTPUT' + str(int(source)) + ':STATE ' + val)
        return

    def get_state(self, source):
        # get state of channel 1 or 2
        self.rp.tx_txt('OUTPUT' + str(int(source)) + ':STATE?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, val

    def set_freq(self, source, val):
        # Set frequency of channel 1 or 2 to a value in Hz.
        # Max value is 62.5e6 Hz
        # For AWG, this is frequency of 1 buffer (16384 samples)
        self.rp.tx_txt('SOUR' + str(int(source)) + ':FREQ:FIX ' + str(int(val)))
        return

    def get_freq(self, source):
        # Get frequency of channel 1 or 2
        self.rp.tx_txt('SOUR' + str(int(source)) + ':FREQ:FIX?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, int(val)

    def set_waveform(self, source, val):
        # Set waveform of chn specified by source.
        # Options are SINE, SQUARE, TRIANGLE, SAWU, SAWD, PWM, ARBITRARY, DC, DC_NEG
        self.rp.tx_txt('SOUR' + str(int(source)) + ':FUNC ' + val)
        return

    def get_waveform(self, source):
        # Get waveform of chn specified by source.
        self.rp.tx_txt('SOUR' + str(int(source)) + ':FUNC?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, val

    def set_amp(self, source, val):
        # Set amplitude of source chn
        # This is amplitude, so pk to pk is twice amplitude and output typically goes from - to + 1V
        self.rp.tx_txt('SOUR' + str(int(source)) + ':VOLT ' + str(val))
        return

    def get_amp(self, source):
        # Get amplitude of source chn
        self.rp.tx_txt('SOUR' + str(int(source)) + ':VOLT?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, float(val)

    def set_offset(self, source, val):
        # Sets offset of source chn
        # Output Typically goes from - to +1 V
        self.rp.tx_txt('SOUR' + str(int(source)) + ':VOLT:OFFS ' + str(val))
        return

    def get_offset(self, source):
        # Gets offset of source chn
        self.rp.tx_txt('SOUR' + str(int(source)) + ':VOLT:OFFS?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, float(val)

    def set_phase(self, source, val):
        # Sets the phase of a channel to the value val
        # in degrees from -360 to 360
        self.rp.tx_txt('SOUR' + str(int(source)) + ':PHAS ' + str(val))
        return

    def get_phase(self, source):
        # Gets the phase of a channel
        self.rp.tx_txt('SOUR' + str(int(source)) + ':PHAS?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, val

    def set_duty_cycle(self, source, val):
        # Set duty cycle of a PWM waveform.
        # from 0 to 1, where 0.5 is 50% for instance
        self.rp.tx_txt('SOUR' + str(int(source)) + ':DCYC ' + str(val))
        return

    def get_duty_cycle(self, source):
        # Get duty cycle of the PWM waveform.
        self.rp.tx_txt('SOUR' + str(int(source)) + ':DCYC?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, float(val)

    def import_awg_data(self, source, data):
        # import data for the awg, should be 16384 samples
        # data should be an array
        data_str = ','.join(str(x) for x in data)
        self.rp.tx_txt('SOUR' + str(int(source)) + ':TRAC:DATA:DATA ' + data_str)
        return

    def get_awg_data(self, source):
        # get stored data
        self.rp.tx_txt('SOUR' + str(int(source)) + ':TRAC:DATA:DATA?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, val

    def set_gen_mode(self, source, val):
        # set mode of this channel to either BURST or CONTINUOUS
        # If burst, will generate R bursts with N signal periods, and P is the time between start time of bursts. Other functions address these values
        self.rp.tx_txt('SOUR' + str(int(source)) + ':BURS:STAT ' + val)
        return

    def get_gen_mode(self, source):
        # Get generation mode for this channel
        self.rp.tx_txt('SOUR' + str(int(source)) + ':BURS:STAT?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, val

    def set_burst_cycle_num(self, source, val):
        # Set N which is the number of cycles in one burst.
        # From 1 to 50000
        self.rp.tx_txt('SOUR' + str(int(source)) + ':BURS:NCYC ' + int(val))
        return

    def get_burst_cycle_num(self, source):
        # Get the number of cycles in each burst (N)
        self.rp.tx_txt('SOUR' + str(int(source)) + ':BURS:NCYC?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, int(val)

    def set_burst_repeats(self, source, val):
        # Set R, the number of repeated bursts.
        # From 1 to 50000
        # 65536 is an infinite number of repetitions
        self.rp.tx_txt('SOUR' + str(int(source)) + ':BURS:NOR ' + int(val))
        return

    def get_burst_repeats(self, source):
        # Get the number of repeated bursts (R)
        self.rp.tx_txt('SOUR' + str(int(source)) + ':BURS:NOR?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, int(val)

    def set_burst_int(self, source, val):
        # Set P, the burst interval from start of one burst to another
        # Units of us, from 1 us to 500 s.
        self.rp.tx_txt('SOUR' + str(int(source)) + ':BURS:INT:PER ' + int(val))
        return

    def get_burst_int(self, source):
        # Get the burst interval from start of one burst to another in us
        self.rp.tx_txt('SOUR' + str(int(source)) + ':BURS:INT:PER?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, int(val)

    def set_trig_source(self, source, val):
        # Sets trigger source for particular channel to EXT_PE, EXT_NE, INT, GATED
        #INT is internal trigger
        # GATED is gated bursts
        # EXT trigger is a 3V3 CMOS signal
        self.rp.tx_txt('SOUR' + str(int(source)) + ':TRIG:SOUR ' + val)
        return

    def get_trig_source(self, source):
        # Get trigger source for this channel
        self.rp.tx_txt('SOUR' + str(int(source)) + ':TRIG:SOUR?')
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, val

    def trigger_all_now(self):
        # Triggers all channels now
        self.rp.tx_txt('SOUR:TRIG:INT')
        return

    def trigger_chn_now(self, source):
        # Trigger chn now
        self.rp.tx_txt('SOUR' + str(int(source)) + ':TRIG:INT')
        return

    def reset(self):
        # Reset generator to default settings
        self.rp.tx_txt('GEN:RST')
        return

    def align_phases(self):
        # Align output phases of both channels
        self.rp.tx_txt('PHAS:ALIGN')
        return
