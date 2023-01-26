"""
Module XEM7305_photon_counter

Usage: 
  Unit of periods: ns.
"""

import ok
import time
import sys
import ctypes
import numpy as np

class XEM7305_photon_counter:
    def __init__(self, dev_serial='', bit_file='photon_counter.bit', counting_period=100000,lockin_up_period=10000000, lockin_down_period = 10000000, clock_period=2.173913):  #Unit of periods: ns.
        self._dev_serial = dev_serial # device serial of our FPGA is '2104000VK5'. Open the first FPGA if given a empty serial number ''. Get serial by _device.GetDeviceListSerial(0). 0 ~ the first device.
        self._bit_file = bit_file
        self._counting_period = counting_period
        self._lockin_up_period = lockin_up_period
        self._lockin_down_period = lockin_down_period
        self._clock_period = clock_period
        self._lock_in = 0
        self.init_dev()

    @property
    def dev_serial(self):
        return self._dev_serial

    @dev_serial.setter
    def dev_serial(self, dev_seri):
        self._dev_serial = dev_seri

    @property
    def bit_file(self):
        return self._bit_file

    @bit_file.setter
    def bit_file(self, bit_f):
        self._bit_file = bit_f
        
    @property
    def counting_period(self):
        return self._counting_period

    @counting_period.setter
    def counting_period(self, cnt_period):
        self._counting_period = cnt_period
    
    @property
    def lockin_up_period(self):
        return self._lockin_up_period

    @lockin_up_period.setter
    def lockin_up_period(self, lockinup_period):
        self._lockin_up_period = lockinup_period
        
    @property
    def lockin_down_period(self):
        return self._lockin_down_period

    @lockin_down_period.setter
    def lockin_down_period(self, lockindown_period):
        self._lockin_down_period = lockindown_period
    
    @property
    def clock_period(self):
        return self._clock_period

    @clock_period.setter
    def clock_period(self, clk_period):
        self._clock_period = clk_period

    @property
    def lock_in(self):
        return self._lock_in

    @lock_in.setter
    def lock_in(self, lockin):
        self._lock_in = lockin

    def init_dev(self):
        self._device = ok.okCFrontPanel()
        if (self._device.GetDeviceCount() < 1):
            sys.exit("Error: no Opal Kelly FPGA device.")
        try: 
            self._device.OpenBySerial(self.dev_serial)
            error = self._device.ConfigureFPGA(self.bit_file)
        except:
            sys.exit("Error: can't open Opal Kelly FPGA device by serial number %s" % self.dev_serial)
        if (error != 0):
            sys.exit("Error: can't program Opal Kelly FPGA device by file %s" % self.bit_file)

    def reset_dev(self):
        self._device.SetWireInValue(0x00, 0x02) # reset_fifo = 1. To reset FIFO only
        self._device.UpdateWireIns()
        self._device.SetWireInValue(0x00, 0x00) # de-assertion reset_fifo signal
        self._device.UpdateWireIns()
        time.sleep(0.001) # After Reset de-assertion, wait at least 30 clock cycles before asserting WE/RE signals.
        self._device.SetWireInValue(0x00, 0x01) # reset = 1. To reset other circuits.
        self._device.UpdateWireIns()
        self._device.SetWireInValue(0x00, 0x00) # de-assertion reset signal
        self._device.UpdateWireIns()

    def start_photon_count(self):
        self.lock_in = 0 #not lock_in.
        self._device.SetWireInValue(0x02, int(self.lock_in))
        self._device.SetWireInValue(0x01, int(round(self.counting_period / self.clock_period))) #counting_period, in the unit of counting clock.
        self._device.UpdateWireIns()
        self.reset_dev()
    
    def start_lockin_count(self):
        self.lock_in = 1 #lock_in.
        self._device.SetWireInValue(0x02, int(self.lock_in))
        self._device.SetWireInValue(0x01, int(self.counting_period / self.clock_period)) #counting_period, in the unit of counting clock.
        self._device.SetWireInValue(0x03, int(self.lockin_up_period / self.clock_period)) #lockin_up_period, in the unit of counting clock.
        self._device.SetWireInValue(0x04, int(self.lockin_down_period / self.clock_period)) #lockin_down_period, in the unit of counting clock.
        self._device.UpdateWireIns()
        self.reset_dev()
        
    def pipe_out(self, buff):
        self._device.ReadFromPipeOut(0xA0, buff) 
        
    # def photon_count(self):
        # self._device.UpdateWireOuts()
        # return self._device.GetWireOutValue(0x20)
    
    # def tdiff_count(self):
        # self._device.UpdateWireOuts()
        # return self._device.GetWireOutValue(0x21)

    # def read_triggered(self):
        # self._device.UpdateTriggerOuts()
        # return self._device.IsTriggered(0x60, 1)


# here are demos for the using this module.        
if __name__ == '__main__':
    dev = XEM7305_photon_counter()
    k = 0
    buff = [bytearray(4*1024), bytearray(4*1024), bytearray(4*1024), bytearray(4*1024), bytearray(4*1024), bytearray(4*1024), bytearray(4*1024), bytearray(4*1024), bytearray(4*1024)]
    ia_out = [[], [], [], [], [], [], [], [], []]  #arrays of integers. the counting results. 

    #demo1: start the counter on FPGA, then pipeout 9 times the counted values.
    dev.counting_period = 100000 #Unit of periods: ns.
    dev.lockin_up_period = 10000000
    dev.lockin_down_period = 10000000
    
    dev.start_photon_count()
    #dev.start_lockin_count()
    while (k < 9):
        dev.pipe_out(buff[k])
        k = k+1
    
    pre_value = 0
    for j in range(9):
        for i in range(1024):
            cur_value = int.from_bytes(buff[j][i*4:i*4+4], "little")
            if (dev.lock_in == 1 and cur_value > 4200000000): # under flow processing: hard-coding. Might have better solution.
                cur_value = cur_value - 4294967296 
            ia_out[j].append(cur_value)
            
            ### Codes to check the wrong count for dev.counting_period = 100000 and pulse frequency 50MHz
            # if (cur_value - pre_value >= 0 and (cur_value - pre_value > 550 or cur_value - pre_value < 450)):
                # print("error: #ia, #elem: ", j, i)
            # elif (cur_value - pre_value < 0 and (pre_value - cur_value > 550 or pre_value - cur_value < 450)):
                # print("error: #ia, #elem: ", j, i)
            
            pre_value = cur_value
        
        
    print(buff[0][:512])
    print(buff[0][4*1024-512:4*1024])
    print(buff[1][:512])
    print(buff[1][4*1024-512:4*1024])
    print(buff[2][:512])
    print(buff[2][4*1024-512:4*1024])
    print(buff[4][:512])
    print(buff[4][4*1024-512:4*1024])
    
    print("ia[0]")
    print(ia_out[0][:64])
    print(ia_out[0][64:512])
    print(ia_out[0][1*1024-64:1*1024])
    print("ia[1]")
    print(ia_out[1][:64])
    print(ia_out[1][64:512])
    print(ia_out[1][1*1024-64:1*1024])
    print("ia[2]")
    print(ia_out[2][:64])
    print(ia_out[2][64:512])
    print(ia_out[2][1*1024-64:1*1024])
    print("ia[3]")
    print(ia_out[3][:64])
    print(ia_out[3][64:512])
    print(ia_out[3][1*1024-64:1*1024])
    print("ia[4]")
    print(ia_out[4][:64])
    print(ia_out[4][64:512])
    print(ia_out[4][1*1024-64:1*1024])
    print("ia[7]")
    print(ia_out[7][:64])
    print(ia_out[7][64:512])
    print(ia_out[7][1*1024-64:1*1024])
    print("ia[8]")
    print(ia_out[8][:64])
    print(ia_out[8][64:512])
    print(ia_out[8][512:1*1024-64])
    print(ia_out[8][1*1024-64:1*1024])
    
    del dev

