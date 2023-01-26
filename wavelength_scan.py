# -*- coding: utf-8 -*-
"""
Created on Fri Oct  7 10:36:21 2022

@author: Zhenghan Yuan

For )
"""
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






# %% for the wavemeter



import socket
import pickle

# IP address and TCP port of server
host = '192.168.1.56'
port = 5353

# Connect to server, display error if connection fails
ClientSocket = socket.socket()
print('Waiting for connection')
try:
    ClientSocket.connect((host, port))
    print('Connected!')
except socket.error as e:
    print(str(e))

# Define global variable which will store the wavelength
# Starting values are Off 
selec_list = [['Off'], ['Off'], ['Off'], ['Off'], ['Off'], ['Off'], ['Off'], ['Off']]

#select desired channel of wavemeter here
cha_num = 3
selec_list[cha_num-1] = 'On'


# Initial time measurement
ti = time.perf_counter()
            

# here are demos for the using this module.        
if __name__ == '__main__':
    n = 100
    j = 0
    dev = XEM7305_photon_counter()
    k = 0
    buff = [ bytearray(4*1024) for _ in range(n)]
    ia_out = [ [] for _ in range(n)]

    #demo1: start the counter on FPGA, then pipeout 9 times the counted values.
    dev.counting_period = 100000 #Unit of periods: ns.
    dev.lockin_up_period = 100000*512
    dev.lockin_down_period = 100000*512
    dev.start_photon_count()
    #dev.start_lockin_count() 
    
    # By toggle between the two lines above to switch between normal counting mode and lock-in counting mode 
    


# %% Acquisition
    
    images=[]
    wl = []
    
    while j<n:
        dev.pipe_out(buff[j])
        for i in range(1024):
            cur_value = int.from_bytes(buff[j][i*4:i*4+4], "little")
            if (dev.lock_in == 1 and cur_value > 4200000000): # under flow processing: hard-coding. Might have better solution.
                cur_value = cur_value - 4294967296 
            ia_out[j].append(cur_value)
            pre_value = cur_value
            #print(f"{i}/{n}")
        count = ia_out[j][1023] - ia_out[j][0]
        
        
        # Pickles and sends selection list    
        to_send = pickle.dumps(selec_list)
        ClientSocket.sendall(to_send)
        # Reads in the length of the message to be received
        length = ClientSocket.recv(8).decode()
        
        
        msg = []
        # # Reads data sent from the host, stores in msg until full message is received
        while len(b"".join(msg)) < int(length):
         	temp = ClientSocket.recv(8192)
         	msg.append(temp)
    
        # Unpickle msg
        data = pickle.loads(b"".join(msg))
    
        # Store wavelength and interferometer data in separate lists
        wvl_data = data[0]
        print(j)
        #int_data = data[1]
        
        #cha_num = 7
    
        #extract wavelength of chosen channel
        selec_cha_wavelength = wvl_data[cha_num-1]
        print(selec_cha_wavelength)
        wvl = float(selec_cha_wavelength)
        wl.append(wvl)  
    
        images.append(count)
        j = j+1
    
    # %% Data Analysis
    #count = []
    # for a in np.arange(n):
    #     # additional chamber, tube oven
    #     # ct = np.sum(images[a][377][310:325])
    #     # experimental chamber, smaller (0.2 mm diameter) arperture 
    #     ct = np.sum(images[a][217:307, 235:301])
    #     count.append(ct)
    wl_array = np.array(wl)
    plt.plot(np.arange(n),images, 'b')
    plt.xlabel('Capture count')
    plt.ylabel('pixel count', color='b')
    
    noise = np.load('noise.npy')
    # plt.plot(noise[:len(count)], 'k', alpha=0.5)
    plt.axhline(np.mean(noise), color='k', alpha=0.5)
    
    plt.axhline(np.quantile(count, 0.99), color='g', linestyle=':')
    
    center_wl = np.round(np.mean(wl_array), 5)
    plt.gca().twinx().plot(np.arange(n),wl_array-center_wl, 'r')
    plt.ylabel('$\Delta \lambda_{center}$ (nm)', color='r')
    
    c = 299792458
    scan_freq = np.round(c/(center_wl**2)*np.ptp(wl_array), 2)
    plt.title(f'$\lambda_{{center}}={center_wl}$nm scan of {scan_freq}GHz')
    fig1 = plt.figure()
    plt.show()
    # %% Further Analysis
    
    # binning by wavelength
    bin_n = 50
    bin_edges = np.linspace(min(wl_array), max(wl_array), bin_n+1)
    bin_int = bin_edges[1]-bin_edges[0]
    ave_count = []
    bin_count = []
    wl_count = np.array([[_wl, c] for _wl, c in sorted(zip(wl_array, images))]).T
    
    plt.scatter(wl_count[0], wl_count[1], marker='.', alpha=0.3)
    #plt.axhline(np.mean(noise), color='k', alpha=0.5)
    plt.show()
    
    i = 1
    while True:
        close_bin = False
        for j, _wl in enumerate(wl_count[0]):
            if _wl > bin_edges[i]:
                ave_count.append(np.mean(wl_count[1][:j+1]))
                bin_count.append(wl_count[1][:j+1])
                wl_count = wl_count[:, j:]
                i += 1
                close_bin = True
                break
        if not close_bin:
            ave_count.append(np.mean(wl_count[1]))
            bin_count.append(wl_count[1])
            break
    
    bin_wl = np.array([np.mean(bin_edges[i:i+1]) for i in range(len(bin_edges)-1)])
    plt.plot(bin_wl, ave_count, 'k')
    spread = 0.3
    for i, _wl in enumerate(bin_wl):
        plt.scatter((np.random.rand(len(bin_count[i]))*spread-spread/2)*bin_int+_wl, bin_count[i], marker='.', alpha=0.1)
    #plt.axhline(np.mean(noise), color='k', alpha=0.5)
    fig2 = plt.figure()
    plt.show()
    # %% Fitting Voigt model
    
    from lmfit.models import VoigtModel, ConstantModel
    
    model = VoigtModel() + ConstantModel()
    
    noise_lvl = np.mean(noise)
    # http://dx.doi.org/10.1103/PhysRevA.83.012502
    linewidth_to_gamma = 34.6e6*(422.7917102e-9**2)/c * 0.5e9
    params = model.make_params(amplitude=0.500, center=422.7915, 
                               sigma=0.0001, gamma=linewidth_to_gamma, c=noise_lvl)
    params['center'].min = bin_edges[0]
    params['center'].max = bin_edges[-1]
    params['amplitude'].min = 0.
    params['gamma'].vary = False
    params['gamma'].expr = ''
    
    wl_count = np.array([[_wl, c] for _wl, c in sorted(zip(wl_array, count))]).T
    
    result = model.fit(wl_count[1], params, x=wl_count[0])
    print(result.fit_report())
    
    plt.scatter(wl_count[0], wl_count[1], marker='.', alpha=0.3)
    plt.plot(bin_wl, result.eval(x=bin_wl), 'r-', label='Voigt fit')
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Pixel count')
    
    plt.legend()
    
    sigma_to_linewidth = 2.3548 * c/((result.values['center'])**2)*(result.values['sigma'])
    print('\nbroadening ', sigma_to_linewidth, 'GHz')
    
    plt.title(f"$\lambda=${result.values['center']}nm")
    
    # %%
    
    plt.imshow(images[np.argmax(count)], cmap='Greys_r')
    # TODO set the max color to the max pixel of interest
    
    # %% Save background noise data
    
    # change the description when new noise data is obtained, uncomment as necessary
    #np.save('noise.npy', count)
    
    
        

