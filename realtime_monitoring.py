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
import matplotlib.pyplot as plt

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
    try:
        del dev
    except Exception:
        pass
    dev = XEM7305_photon_counter()
    k = 0

    ################
    # Three functions in total, toggle between them by commenting others 
    ################

    
    #%% For real-time monitoring (function 1)
    #main purpose of this section is to be a real-time monitor for adjusting the position of pinhole
    
    dev.counting_period = 200000 #Unit of periods: ns.
    # dev.lockin_up_period = 10000000
    # dev.lockin_down_period = 10000000
    dev.lockin_up_period = 0
    dev.lockin_down_period = 100000
    buff = [ bytearray(4*1024) for _ in range(50000)]
    ia_out = [ [] for _ in range(50000)]
    ia_out[0] = [0]
    from matplotlib.animation import FuncAnimation
    fig, ax = plt.subplots()
    y = []
    x = []
    def animate(k,x,y):
        
        dev.pipe_out(buff[k])
        for i in range(1024):
            cur_value = int.from_bytes(buff[k][i*4:i*4+4], "little")
            ia_out[k].append(cur_value)
            if (dev.lock_in == 1 and cur_value > 4200000000): # under flow processing: hard-coding. Might have better solution.
                cur_value = cur_value - 4294967296
            # t = i*dev.counting_period*1e-9+k*1024*dev.counting_period*1e-9
            # y.append(ia_out[k][i])
            # x.append(t)
        t = k*1024*dev.counting_period*1e-9
        y.append(ia_out[k][0]-ia_out[k-1][0])
        x.append(t)
        k = k+1
            
        
        x = x[-500:]
        y = y[-500:]
        ax.clear()
        ax.plot(x, y)
        ax.set_ylabel('Count per 1024*counting period')
        ax.set_xlabel('timeline/s')

        ax.axhline(np.mean(y), linestyle=':', color='r', label=f"{int(x[-1]-x[0])}s average")
        index_to_second = 1024*dev.counting_period*1e-9
        ten_second_to_index = int(10/index_to_second)
        ax.axhline(np.mean(y[-ten_second_to_index:]), linestyle=':', color='g', label='10s average')
        #ax.set_xlim([0,200])
        #ax.set_ylim([0,10])
        
        
    dev.start_photon_count()  
    #ani = FuncAnimation(fig, animate, frames=range(1,len(buff)+1), interval=dev.counting_period*1e-6*1024,fargs=(x,y), repeat=False)    
    ani = FuncAnimation(fig, animate, frames=range(1,len(buff)+1), interval=0,fargs=(x,y), repeat=False)    
    plt.legend()
    plt.show()


    

    
    
    
    #%% real-time monitoring with lockin signal (function 2)
    # # for taking the lockin count over a certain period of time
    # dev.counting_period =1e5
    # #Unit of periods: ns, the absolute limit of this value is from 0 to 2.1739*2^32 ns 
    # # however some technical issues may happen if it is set to be really low
    # #please consult Seigen
    # dev.lockin_up_period = 1e5*512
    # dev.lockin_down_period = 1e5*512
    
    # # The 512 is because there are 1024 data points per buffer, the lockin period is
    # # synchronised only if the multiplier is 512 as we take one data point from per 1024 data points. 
    # # only 50% duty cycle is considered in this case to subtract all the noise
    
    # n = 1000
    # # by setting number of empty lists, total measuring time can be set, which equals to n*1024*counting_period
    # buff = [ bytearray(4*1024) for _ in range(n)]
    # ia_out = [ [] for _ in range(n)]
    # # by setting number of empty lists, total measuring time can be set, which equals to n
    # from matplotlib.animation import FuncAnimation
    # fig, ax = plt.subplots()
    # y = []
    # x = []
    # def animate(k,x,y):
        
    #     dev.pipe_out(buff[k])
        
    #     for i in range(1024):
    #         cur_value = int.from_bytes(buff[k][i*4:i*4+4], "little")
    #         if (dev.lock_in == 1 and cur_value > 4200000000): # under flow processing: hard-coding. Might have better solution.
    #             cur_value = cur_value - 4294967296
    #         ia_out[k].append(cur_value)
    #         # t = i*dev.counting_period*1e-9+k*1024*dev.counting_period*1e-9
    #         # y.append(ia_out[k][i])
    #         # x.append(t)
            
    #     t = k*1024*dev.counting_period*1e-9
    #     y.append(ia_out[k][0])
    #     x.append(t)
    #     k = k+1
            
        
    #     x = x[-1000:] # to set the number of data points in every frame 
    #     y = y[-1000:]
        
    #     ax.clear()
    #     ax.plot(x, y)
    #     ax.set_ylabel('Effective Count Accumulated')
    #     ax.set_xlabel('timeline/s')

    #     #ax.set_xlim([0,200])
    #     #ax.set_ylim([0,10])
        
        
    # dev.start_lockin_count() 
    # time.sleep(0.1024)
    # ani = FuncAnimation(fig, animate, frames=range(len(buff)), interval=dev.counting_period*1e-6*1024,fargs=(x,y), repeat=False)   
    # plt.show()
    
    
    # #%% To differentiate the plot above (function 3)
    
    dev.counting_period =2e5

    dev.lockin_up_period = 10000 #1e5*512
    dev.lockin_down_period = 10000 #1e5*512
    
    
    

    
    n = 10000
    # by setting number of empty lists, total measuring time can be set, which equals to n*1024*counting_period
    buff = [ bytearray(4*1024) for _ in range(n)]
    ia_out = [ [] for _ in range(n)]
    ia_out[0] = [0]
    # by setting number of empty lists, total measuring time can be set, which equals to n
    from matplotlib.animation import FuncAnimation
    fig, ax = plt.subplots()
    y = []
    x = []
    def animate(k,x,y):
        
        dev.pipe_out(buff[k])
        for i in range(1024):
            cur_value = int.from_bytes(buff[k][i*4:i*4+4], "little")
            
            if (dev.lock_in == 1 and cur_value > 4200000000): # under flow processing: hard-coding. Might have better solution.
                cur_value = cur_value - 4294967296
            ia_out[k].append(cur_value)
            # t = i*dev.counting_period*1e-9+k*1024*dev.counting_period*1e-9
            # y.append(ia_out[k][i])
            # x.append(t)
        t = k*1024*dev.counting_period*1e-9
        y.append(ia_out[k][0]-ia_out[k-1][0])
        x.append(t)
        k = k+1
            
        
        x = x[-1000:] # to set the number of data points in every frame 
        y = y[-1000:]
        
        ax.clear()
        ax.plot(x, y)
        ax.set_ylabel('Count gained per Lock-in period')
        ax.set_xlabel('timeline/s')

        #ax.set_xlim([0,200])
        #ax.set_ylim([0,10])
        
        
    dev.start_lockin_count() 
    time.sleep(0.1024)
    ani = FuncAnimation(fig, animate, frames=range(1,len(buff)+1), interval=dev.counting_period*1e-6*1024,fargs=(x,y), repeat=False)    
    plt.grid()
    plt.show()
    plt.grid()