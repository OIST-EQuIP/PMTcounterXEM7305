import XEM7305_photon_counter as phc
import time 
# get the device
dev = phc.XEM7305_photon_counter()

k = 0
buff = [bytearray(4*1024), bytearray(4*1024), bytearray(4*1024), bytearray(4*1024), bytearray(4*1024), bytearray(4*1024), bytearray(4*1024), bytearray(4*1024), bytearray(4*1024)]
ia_out = [[], [], [], [], [], [], [], [], []]  #arrays of integers. the counting results. 

#demo1: start the counter on FPGA, then pipeout 9 times the counted values.
dev.counting_period = 100000 #Unit of periods: ns.
dev.lockin_up_period = 10000000
dev.lockin_down_period = 10000000

#dev.start_photon_count() # normal counting 
dev.start_lockin_count() # lock-in counting 
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


