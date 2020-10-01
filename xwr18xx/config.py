import math

C = 299792458  # speed of light in m/s


def count_set_bits(n):
    'Counts the number of set bits in a number'

    count = 0
    while n:
        n &= n - 1
        count += 1

    return count


class Config:
    def __init__(self, config_filename):
        self.config_filename = config_filename
        self.parse()

    def parse(self):
        try:
            with open(self.config_filename) as lines:
                self.config_file = [line.rstrip('\r\n') for line in lines]
        except Exception as e:
            print(e)
            print('Failed to read the configuration file')

        for config in self.config_file:
            tokens = config.split(' ')

            # channelCfg rxChannelEn txChannelEn cascading
            if tokens[0] == 'channelCfg':
                self.num_rx_ant = count_set_bits(int(tokens[1]))
                self.num_tx_ant = count_set_bits(int(tokens[2]))
            # adcCfg numADCBits adcOutputFmt
            elif tokens[0] == 'adcCfg':
                self.adc_output_fmt = int(tokens[2])
            # profileCfg profileId startFreq idleTime adcStartTime rampEndTime txOutPower txPhaseShifter freqSlopeConst txStartTime numAdcSamples digOutSampleRate hpfCornerFreq1 hpfCornerFreq2 rxGain
            elif tokens[0] == 'profileCfg':
                self.start_freq = float(tokens[2])  # GHz
                self.idle_time = float(tokens[3])  # u-sec
                self.ramp_end_time = float(tokens[5])  # u-sec
                self.freq_slope_const = float(tokens[8])  # MHz/u-sec
                self.num_adc_samples = int(tokens[10])
                self.dig_out_sample_rate = int(tokens[11])  # ksps
            # frameCfg chirpStartIndex chirpEndIndex numberOfLoops numberOfFrames framePeriodicity triggerSelect frameTriggerDelay
            elif tokens[0] == 'frameCfg':
                chirp_start_idx = int(tokens[1])
                chirp_end_idx = int(tokens[2])
                self.number_of_loops = int(tokens[3])
                self.chirps_per_frame = (
                    chirp_end_idx - chirp_start_idx + 1) * self.number_of_loops
                self.frame_periodicity = int(tokens[5])

        try:
            # FFT size is a power of 2
            self.range_fft_size = 2 ** int(
                math.ceil(math.log2(self.num_adc_samples)))
            self.doppler_fft_size = self.number_of_loops

            if self.adc_output_fmt == 1:
                IF_max = 0.9 * self.dig_out_sample_rate * 1e3
            else:
                IF_max = 0.9 * self.dig_out_sample_rate * 1e3 / 2

            adc_sampling_time = self.num_adc_samples / \
                (self.dig_out_sample_rate * 1e3)
            Tc = (self.idle_time + self.ramp_end_time) * 1e-6
            Fc = self.start_freq * 1e9
            Fs = self.dig_out_sample_rate * 1e3
            S = self.freq_slope_const * 1e12
            B = S * adc_sampling_time
            wave_len = C / Fc

            # Calculate the radar characteristics
            # Note the multiplication of Tc by num_tx_ant in doppler calculations as given by TDM-MIMO theory

            self.range_resolution = C / (2 * B)
            self.doppler_resolution = wave_len / \
                (2 * self.number_of_loops * self.num_tx_ant * Tc)

            self.range_max = IF_max * C / (2 * S)
            self.doppler_max = wave_len / (4 * Tc * self.num_tx_ant)
        except Exception as e:
            print(e)
            print(
                'Failed to calculate operation parameters, check if configuration file is valid')

        return self
