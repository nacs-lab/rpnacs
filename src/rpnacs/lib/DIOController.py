from . import utils

class DIOController:
    def __init__(self, rp):
        # rp is a redpitaya_scpi object defined in the file redpitaya_scpi.py file. It will handle all of the communication with the RedPitaya
        self.rp = rp

    ## Higher Level API
    def set_led(self, num, state):
        # num is from 0 to 8
        # state is 0 or 1
        identifier = 'LED' + str(int(num))
        self.set_state(identifier, state)
        return

    def get_led(self, num):
        # returns state of LED which has num = 0 to 8
        identifier = 'LED' + str(int(num))
        return self.get_state(identifier, state)

    def set_all_led(self, states):
        # states is a list of 0s and 1s for the LEDS 0 to 8, total of 9
        if len(states) != 9:
            return
        for i in range(9):
            self.set_led(i, states[i])
        return

    def set_pin_direction(self, num, direction, pin_type = 'P'):
        # pin_type can also be 'N'. Not sure what the difference is, but they are different pins.
        # direction is 'OUT' or 'IN'
        # num is from 0 to 7
        identifier = 'DIO' + str(int(num)) + '_' + pin_type
        self.set_direction(identifier, direction)
        return

    def get_pin_direction(self, num, pin_type = 'P'):
        # get pin direction from chn from 0 to 7. pin_type can also be 'N'
        identifier = 'DIO' + str(int(num)) + '_' + pin_type
        return self.get_direction(identifier)

    def set_all_pin_direction(self, direction, pin_type = 'P'):
        # Sets all pin directions to array of directions, If P type pins, avoids DIO0_P which is EXT_TRIG
        if pin_type == 'P':
            for i in range(7):
                if len(direction) == 7:
                    self.set_pin_direction(i + 1, direction[i], 'P')
        elif pin_type == 'N':
            for i in range(8):
                if len(direction) == 8:
                    self.set_pin_direction(i, direction[i], 'N')
        return

    def set_pin_state(self, num, state, pin_type = 'P'):
        # set pin state,num from 0 to 7. state is 0 or 1
        identifier = 'DIO' + str(int(num)) + '_' + pin_type
        self.set_state(identifier, state)
        return

    def get_pin_state(self, num, pin_type = 'P'):
        # get pin state, num from 0 to 7. Returns 0 or 1
        identifier = 'DIO' + str(int(num)) + '_' + pin_type
        return self.get_state(identifier)

    def set_all_pin_states(self, states, pin_type = 'P'):
        # Sets all pin states to array of states.
        # States should be array of length 8 for N and length 7 for P
        if pin_type == 'P':
            if len(states) == 7:
                for i in range(7):
                    self.set_pin_state(i + 1, states[i], 'P')
        elif pin_type == 'N':
            if len(states) == 8:
                for i in range(8):
                    self.set_pin_state(i, states[i], 'N')
        return

    ## Lower level API
    def reset(self):
        # Set digital pin to default values, digital ios set to input and are on low. LEDs to OFF
        self.rp.tx_txt('DIG:RST')
        return

    def set_direction(self, identifier, direction):
        # Set direction of this pin
        self.rp.tx_txt('DIG:PIN:DIR ' + direction + ',' + identifier)
        return

    def get_direction(self, identifier):
        # Get direction of this pin
        self.rp.tx_txt('DIG:PIN:DIR? ' + identifier)
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, val

    def set_state(self, identifier, state):
        # Set state of this pin
        self.rp.tx_txt('DIG:PIN ' + identifier + ',' + str(int(state)))
        return

    def get_state(self, identifier):
        # Get state of this pin
        self.rp.tx_txt('DIG:PIN? ' + identifier)
        err_flag, val = utils.rm_err(self.rp.rx_txt())
        return err_flag, int(val)
