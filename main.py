import hid
import struct
import time

vid = 0x2FE3	# Change it for your device
pid = 0x0001	# Change it for your device

# Get the HID device path, this happens to be the second device defined. May need to find another 
# way to identify which device is which but this works for now.

path = hid.enumerate(vid, pid)[1]['path']

# To read from the device, h.read
# To write to the device, h.write is used

'''
Send data to the device in this format:
struct raw_hid_packet {
    uint8_t report_id;
    uint16_t seq_id;
    uint8_t data[29];
};
'''

with hid.Device(path=path) as h:
    print(f'Device manufacturer: {h.manufacturer}')
    print(f'Product: {h.product}')
    print(f'Serial Number: {h.serial}')
    message = bytes([x for x in range(1,33)])
    h.write(message)
    print(message)
    time.sleep(1)

