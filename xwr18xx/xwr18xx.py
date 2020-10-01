import serial
import time
from struct import Struct, pack, unpack
from collections import namedtuple
from .config import Config
from .tlv import TLV

# encode magic word in little endian format
MAGIC_WORD = pack('<4H', 0x0102, 0x0304, 0x0506, 0x0708)

HeaderStruct = Struct('<8I')
Header = namedtuple('Header', ['version', 'totalPacketLen', 'platform',
                               'frameNumber', 'timeCpuCycles', 'numDetectedObj', 'numTLVs', 'subFrameNumber'])


class XWR18xx:
    '''Texas Instrument's XWR18xx mmWave Automotive Radar Sensor'''

    def __init__(self, config_filename, cli_port, data_port, timeout=1, debug=False):
        self.cli_port = serial.Serial(cli_port, 115200)
        self.data_port = serial.Serial(data_port, 921600, timeout=timeout)

        self.config = Config(config_filename)
        self.tlv = TLV(self.config)

        self.debug = debug

    def write(self, data):
        'Write data to CLI serial port'
        if self.debug:
            print(data)
        self.cli_port.write((data + '\n').encode())
        self.cli_port.flush()
        time.sleep(10e-3)

    def close(self):
        'Close connection with the board'
        self.write('sensorStop')

    def load_config(self):
        'Load configuration file onto the board'
        self.config.parse()
        for config in self.config.config_file:
            self.write(config)

    def read_header(self):
        'Read incoming packet header'

        # read until it finds the magic word (for syncing)
        magic_word = self.data_port.read_until(MAGIC_WORD)

        retry = 0
        while MAGIC_WORD not in magic_word and retry < 2:
            if retry == 0 and self.debug:
                print('Failed to read magic word')
                print('Retrying')

            retry += 1
            magic_word = self.data_port.read_until(MAGIC_WORD)

            if len(magic_word) == 0 and retry == 1:
                if self.debug:
                    print('Failed to read any data')
                    print('Reloading config file')
                self.load_config()

            if len(magic_word) == 0 and retry == 2:
                if self.debug:
                    print('No success')
                print('Try to reset the board')

        if MAGIC_WORD not in magic_word:
            raise Exception('Failed to read magic word')

        # read the header
        header_bytes = self.data_port.read(HeaderStruct.size)

        if len(header_bytes) != HeaderStruct.size:
            raise Exception('Failed to read header')

        header = Header(*HeaderStruct.unpack(header_bytes))

        return header

    def read_packet(self, header):
        'Read packet content according to the header'
        remaining = header.totalPacketLen - HeaderStruct.size - len(MAGIC_WORD)
        packet_bytes = self.data_port.read(remaining)

        return packet_bytes

    def read_raw(self):
        'Read raw packet'
        header = self.read_header()

        packet_bytes = self.read_packet(header)

        packet = {0: header}

        for t, v in self.tlv.parse_raw(packet_bytes):
            packet[t] = v

        return packet

    def read(self):
        'Read structured packet'
        header = self.read_header()

        packet_bytes = self.read_packet(header)

        packet = {0: header}

        for t, v in self.tlv.parse(packet_bytes, header):
            packet[t] = v

        return packet
