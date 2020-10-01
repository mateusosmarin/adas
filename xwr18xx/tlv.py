from struct import Struct, pack, unpack
from collections import namedtuple
from enum import IntEnum
import numpy as np

MessageStatsStruct = Struct('<6I')
MessageStats = namedtuple('MessageStats', ['interFrameProcessingTime', 'transmitOutputTime',
                                           'interFrameProcessingMargin', 'interChirpProcessingMargin', 'activeFrameCPULoad', 'interFrameCPULoad'])
TLStruct = Struct('<2I')


class MmwDemoOutputMessageType(IntEnum):
    'mmWave output message type enum'
    MMWDEMO_OUTPUT_MSG_HEADER = 0
    MMWDEMO_OUTPUT_MSG_DETECTED_POINTS = 1
    MMWDEMO_OUTPUT_MSG_RANGE_PROFILE = 2
    MMWDEMO_OUTPUT_MSG_NOISE_PROFILE = 3
    MMWDEMO_OUTPUT_MSG_AZIMUT_STATIC_HEAT_MAP = 4
    MMWDEMO_OUTPUT_MSG_RANGE_DOPPLER_HEAT_MAP = 5
    MMWDEMO_OUTPUT_MSG_STATS = 6
    MMWDEMO_OUTPUT_MSG_DETECTED_POINTS_SIDE_INFO = 7
    MMWDEMO_OUTPUT_MSG_AZIMUT_ELEVATION_STATIC_HEAT_MAP = 8
    MMWDEMO_OUTPUT_MSG_TEMPERATURE_STATS = 9
    MMWDEMO_OUTPUT_MSG_MAX = 10


class TLV:
    'TLV format parser for AWR18xx mmWave radar board'

    def __init__(self, config):
        self.config = config

    def parse_raw(self, data):
        '''
        parse_raw(data) -> type, value

        Generator which parses TLV data (bytes) into type and raw value
        '''

        tl_length = TLStruct.size

        while len(data) > TLStruct.size:
            t, l = TLStruct.unpack(data[:tl_length])
            data = data[tl_length:]

            # Check if type is valid
            if t in MmwDemoOutputMessageType.__members__.values() and len(data) >= l:
                v = unpack(f'{l}B', data[:l])
                data = data[l:]
                yield t, v

    def parse(self, data, header):
        '''
        parse(data, header) -> type, value

        Generator which takes data and header to decode mmWave output format acordingly
        '''

        tl_length = TLStruct.size

        while len(data) > tl_length:
            t, l = TLStruct.unpack(data[:tl_length])
            data = data[tl_length:]

            # Check if type is valid
            if t in MmwDemoOutputMessageType.__members__.values() and len(data) >= l:

                if t == MmwDemoOutputMessageType.MMWDEMO_OUTPUT_MSG_DETECTED_POINTS:
                    # Array of detected objects in [x, y, z, velocity] format
                    v = unpack(f'<{header.numDetectedObj * 4}f', data[:l])
                    v = np.array(v).reshape((header.numDetectedObj, 4))
                    v = np.nan_to_num(v)

                elif t == MmwDemoOutputMessageType.MMWDEMO_OUTPUT_MSG_RANGE_PROFILE:
                    # Profile points at 0th doppler (stationary objects)
                    # The points represent the sum of log2 magnitudes of received antennas expressed in Q9 format
                    range_fft_size = self.config.range_fft_size
                    v = unpack(f'{range_fft_size}H', data[:l])
                    v = np.array(v)
                    v = np.nan_to_num(v)

                elif t == MmwDemoOutputMessageType.MMWDEMO_OUTPUT_MSG_NOISE_PROFILE:
                    # The same format as range profile but the profile is at the maximum doppler bin (maximum speed objects)
                    # In general for stationary scene, there would be no objects or clutter at maximum speed so the range profile at such speed represents the received noise floor
                    range_fft_size = self.config.range_fft_size
                    v = unpack(f'{range_fft_size}H', data[:l])
                    v = np.array(v)
                    v = np.nan_to_num(v)

                elif t == MmwDemoOutputMessageType.MMWDEMO_OUTPUT_MSG_AZIMUT_STATIC_HEAT_MAP:
                    # Azimut static heat map. The antenna data are complex symbols, with imaginary first and real second
                    range_fft_size = self.config.range_fft_size
                    virtual_antennas = self.num_tx * self.num_rx
                    length = range_fft_size * virtual_antennas * 2
                    v = unpack(f'<{length}h', data[:l])
                    v = np.array(v).reshape(
                        (range_fft_size, virtual_antennas, 2))
                    v = np.nan_to_num(v)

                elif t == MmwDemoOutputMessageType.MMWDEMO_OUTPUT_MSG_RANGE_DOPPLER_HEAT_MAP:
                    # The detection matrix. Format is (Range FFT size) x (Doppler FFT size)
                    range_fft_size = self.config.range_fft_size
                    doppler_fft_size = self.config.doppler_fft_size
                    length = range_fft_size * doppler_fft_size
                    v = unpack(f'<{length}H', data[:l])
                    v = np.array(v).reshape((range_fft_size, doppler_fft_size))
                    v = np.nan_to_num(v)

                elif t == MmwDemoOutputMessageType.MMWDEMO_OUTPUT_MSG_STATS:
                    # Timing information from data path
                    v = MessageStatsStruct.unpack(data[:l])
                    v = MessageStats(*v)

                elif t == MmwDemoOutputMessageType.MMWDEMO_OUTPUT_MSG_DETECTED_POINTS_SIDE_INFO:
                    # Array of detected objects side info in [snr, noise] format
                    v = unpack(f'{header.numDetectedObj * 2}h', data[:l])
                    v = np.array(v).reshape((header.numDetectedObj, 2))
                    v = np.nan_to_num(v)

                elif t == MmwDemoOutputMessageType.MMWDEMO_OUTPUT_MSG_AZIMUT_ELEVATION_STATIC_HEAT_MAP:
                    # Samples to calculate static azimuth/elevation heatmap, (all virtual antennas exported) - unused in the demo
                    v = unpack(f'{l}B', data[:l])

                elif t == MmwDemoOutputMessageType.MMWDEMO_OUTPUT_MSG_TEMPERATURE_STATS:
                    # Structure of detailed temperature report as obtained from radar front end
                    v = unpack(f'{l}B', data[:l])

                elif t == MmwDemoOutputMessageType.MMWDEMO_OUTPUT_MSG_MAX:
                    v = unpack(f'{l}B', data[:l])

                data = data[l:]
                yield t, v
