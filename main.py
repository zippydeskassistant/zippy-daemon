import hid
from enum import IntEnum
import struct
import time
import argparse

vid = 0x1067 # Change for your device
pid = 0x626D 

'''
  Image commands
  N.B.:
  - Image names are limited to 54 characters, excluding the null terminator.
  - Image data must be received in proper packet_id order.
    If packets are not sent in order the image will be deleted.

 To create a new image:
 1. Send a create image or create image animated command
    a. Populate the image name, width, and height
    b. For create image animated, populate the frame count and frame delay
 2. Send a number of write image commands
 3. When complete, send a close image command

 To delete an image:
 1. Send a delete image command
    a. Populate the image name

 To choose an image:
 1. Send a choose image command
    a. Populate the image name

 To get the remaining flash space:
 1. Send a flash remaining command

 To format the filesystem:
 1. Send a format filesystem command

 To set the time:
 1. Send a set time command
   a. Populate time as a Unix timestamp

 Return values are:
 report_id | seq_id | return_code
'''

class report_id(IntEnum):
    CREATE_IMAGE = 0x50
    CREATE_IMAGE_ANIMATED = 0x51,
    OPEN_IMAGE = 0x52,
    WRITE_IMAGE = 0x53,
    CLOSE_IMAGE = 0x54,
    DELETE_IMAGE = 0x55,
    CHOOSE_IMAGE = 0x56,
    FLASH_REMAINING = 0x57,
    FORMAT_FILESYSTEM = 0x58,
    SET_TIME = 0x59,

report_id_names = {
    "CREATE_IMAGE": report_id.CREATE_IMAGE,
    "CREATE_IMAGE_ANIMATED": report_id.CREATE_IMAGE_ANIMATED,
    "OPEN_IMAGE": report_id.OPEN_IMAGE,
    "WRITE_IMAGE": report_id.WRITE_IMAGE,
    "CLOSE_IMAGE": report_id.CLOSE_IMAGE,
    "DELETE_IMAGE": report_id.DELETE_IMAGE,
    "CHOOSE_IMAGE": report_id.CHOOSE_IMAGE,
    "FLASH_REMAINING": report_id.FLASH_REMAINING,
    "FORMAT_FILESYSTEM": report_id.FORMAT_FILESYSTEM,
    "SET_TIME": report_id.SET_TIME
}

class raw_hid_packet:
    def __init__(self, packet_id, seq_id, data):
        if packet_id not in report_id:
            raise ValueError("Invalid report ID")
        self.report_id = packet_id 
        self.seq_id = seq_id
        if type(data) == str:
            data = data.encode()
        self.data = data
        self.data_len = len(data)
        self.packet = self._create_packet()

    def _create_packet(self):
        # Ensure data is not larger than 32 bytes
        assert self.data_len <= 32, "Data length cannot exceed 32 bytes"

        # Create packet with header and data as a struct
        print(f"Packet ID: {self.report_id}")
        print(f"Sequence ID: {self.seq_id}")
        print(f"Data: {self.data}")
        packet = struct.pack("<BBH28p", 0x09, self.report_id, self.seq_id, self.data)
        for i in packet:
            print(format(i, '02x'), end=' ')
        print()
        if (len(packet) > 32):
            raise ValueError("Packet length cannot exceed 32 bytes")
        return bytes(packet)
    
    def __repr__(self):
        return f"{self.packet}"
    
    def __len__(self):
        return self.data_len

class create_image_packet(raw_hid_packet):
    def __init__(self, seq_id, image_name, width, height):
        data = struct.pack("<BB", width, height) + bytes(image_name, 'ascii')
        super().__init__(report_id.CREATE_IMAGE, seq_id, data)

class create_image_animated_packet(raw_hid_packet):
    def __init__(self, seq_id, image_name, width, height, frame_count, frame_delay):
        data = struct.pack("<HHHH", width, height, frame_count, frame_delay) + image_name
        super().__init__(report_id.CREATE_IMAGE_ANIMATED, seq_id, data)

class open_image_packet(raw_hid_packet):
    def __init__(self, seq_id, image_name):
        super().__init__(report_id.OPEN_IMAGE, seq_id, image_name)

class write_image_packet(raw_hid_packet):
    def __init__(self, seq_id, image_data):
        super().__init__(report_id.WRITE_IMAGE, seq_id, image_data)

class close_image_packet(raw_hid_packet):
    def __init__(self, seq_id):
        super().__init__(report_id.CLOSE_IMAGE, seq_id, "")

class delete_image_packet(raw_hid_packet):
    def __init__(self, seq_id, image_name):
        super().__init__(report_id.DELETE_IMAGE, seq_id, image_name)

class choose_image_packet(raw_hid_packet):
    def __init__(self, seq_id, image_name):
        super().__init__(report_id.CHOOSE_IMAGE, seq_id, image_name)

class flash_remaining_packet(raw_hid_packet):
    def __init__(self, seq_id):
        super().__init__(report_id.FLASH_REMAINING, seq_id, "")

class format_filesystem_packet(raw_hid_packet):
    def __init__(self, seq_id):
        super().__init__(report_id.FORMAT_FILESYSTEM, seq_id, "")

class set_time_packet(raw_hid_packet):
    def __init__(self, seq_id, time):
        super().__init__(report_id.SET_TIME, seq_id, struct.pack("<I", time))

parser = argparse.ArgumentParser(description='Send raw HID packets to a device')
# Check if valid packet type
parser.add_argument('--packet_type', type=str, help='Packet type')
parser.add_argument('--seq_id', type=int, help='Sequence ID')
parser.add_argument('--data', type=str, help='Data to send')
args = parser.parse_args()

if args.packet_type is None or args.seq_id is None or args.data is None:
    raise ValueError("Missing required arguments")

if args.packet_type not in report_id_names:
    raise ValueError("Invalid packet type")

packet_type = report_id_names[args.packet_type]
if packet_type is None:
    raise ValueError("Invalid packet type")

match packet_type:
    case report_id.CREATE_IMAGE:
        packet = create_image_packet(args.seq_id, args.data, 128, 128)
    case report_id.CREATE_IMAGE_ANIMATED:
        packet = create_image_animated_packet(args.seq_id, args.data)
    case report_id.OPEN_IMAGE:
        packet = open_image_packet(args.seq_id, args.data)
    case report_id.WRITE_IMAGE:
        packet = write_image_packet(args.seq_id, args.data)
    case report_id.CLOSE_IMAGE:
        packet = close_image_packet(args.seq_id)
    case report_id.DELETE_IMAGE:
        packet = delete_image_packet(args.seq_id, args.data)
    case report_id.CHOOSE_IMAGE:
        packet = choose_image_packet(args.seq_id, args.data)
    case report_id.FLASH_REMAINING:
        packet = flash_remaining_packet(args.seq_id)
    case report_id.FORMAT_FILESYSTEM:
        packet = format_filesystem_packet(args.seq_id)
    case report_id.SET_TIME:
        packet = set_time_packet(args.seq_id, args.data)

path = hid.enumerate(vid, pid)[1]['path']

with hid.Device(path=path) as h:
    print(f'Device manufacturer: {h.manufacturer}')
    print(f'Product: {h.product}')
    print(f'Serial Number: {h.serial}')
    h.write(packet.packet)
    print(h.read(32))
