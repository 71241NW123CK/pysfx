#!/usr/bin/env python

import struct
import wave

# todo: Support sample width other than 2 bytes.
SAMPLE_WIDTH = 2
NORM = 2 ** (8 * SAMPLE_WIDTH - 1) - 1

THIN_BAR = u'\u2500'
THICK_PIPE_LEFT = u'\u2528'
THICK_PIPE_RIGHT = u'\u2520'
THICK_PIPE_LEFT_RIGHT = u'\u2542'
DOUBLE_PIPE = u'\u2551'

def main():
	import cmath
	class _SineWaveSampleSequence(object):
		# todo: reimplement this with complex numbers.
		def __init__(self, sample_rate, frequency, initial_phase=0):
			self.sample_rate = float(sample_rate)
			self.frequency = float(frequency)
			self.initial_phase = float(initial_phase)
			self.phase = cmath.exp(1j * self.initial_phase)
			self.phase_shift_per_sample = cmath.exp(1j * (2.0 * cmath.pi * (self.frequency / self.sample_rate)))
		def next_sample(self):
			result = self.phase.imag
			self.phase *= self.phase_shift_per_sample
			return result
	fn = 'A_440_1s.wav'
	sample_rate = 44100
	frequency = 440
	left_sample_sequence = _SineWaveSampleSequence(sample_rate, frequency)
	right_sample_sequence = _SineWaveSampleSequence(sample_rate, frequency)
	print "writing wav file."
	write_wav_from_sample_sequence_list(fn, [left_sample_sequence, right_sample_sequence], 1)
	print "reading wav file."
	print_string = pretty_print_wav_sample_sequences(fn, 32)
	print "printing wav file."
	print print_string

def write_wav_from_sample_sequence_list(output_filename, sample_sequence_list, duration, sample_rate=44100, safety=True, clamp=False):
	# todo: If safety, check if the output file already exists.  If so, abort foetus.
	f = wave.open(output_filename, 'w')
	f.setparams((len(sample_sequence_list), SAMPLE_WIDTH, sample_rate, 0, 'NONE', 'not compressed'))
	samples_per_channel = int(sample_rate * duration)
	packed_sample_list = []
	for i in range(samples_per_channel):
		for sample_sequence in sample_sequence_list:
			sample = sample_sequence.next_sample()
			# todo: If clamp, clamp the sample to [-1, 1]
			norm_sample = int(NORM * sample)
			packed_sample = struct.pack('h', norm_sample)
			packed_sample_list.append(packed_sample)
	sample_string = ''.join(packed_sample_list)
	f.writeframes(sample_string)

def read_wav_norm_sample_sequences(input_filename):
	f = wave.open(input_filename, 'r')
	(channel_count, sample_width, sample_rate, samples_per_channel, compression_type, compression_name) = f.getparams()
	packed_sample_list = f.readframes(channel_count * samples_per_channel)
	interleaved_norm_samples = struct.unpack_from("%dh" % samples_per_channel * channel_count, packed_sample_list)
	return [interleaved_norm_samples[i::channel_count] for i in range(channel_count)]

def pretty_print_wav_sample_sequences(input_filename, half_width):
	norm_sample_sequence_list = read_wav_norm_sample_sequences(input_filename)
	channel_index = 0
	result_lines = []
	for norm_sample_sequence in norm_sample_sequence_list:
		result_lines.append('channel %d\n' % channel_index)
		sample_index = 0
		for norm_sample in norm_sample_sequence:
			sample_index_string = '%09d' % sample_index # enough for 1 hour at 44100 Hz
			signal_chars = (1 + 2 * half_width) * [' ']
			sample = float(norm_sample) / NORM
			wide_sample = int(round(sample * half_width))
			if wide_sample < 0:
				for i in range(half_width + wide_sample, half_width):
					signal_chars[i] = THIN_BAR
				signal_chars[half_width] = THICK_PIPE_LEFT
			elif wide_sample > 0:
				for i in range(half_width + 1, half_width + wide_sample + 1):
					signal_chars[i] = THIN_BAR
				signal_chars[half_width] = THICK_PIPE_RIGHT
			signal_chars[half_width + wide_sample] = THICK_PIPE_LEFT_RIGHT
			signal_string = ''.join(signal_chars)
			result_lines.append('%s %s %s %s\n' % (sample_index_string, DOUBLE_PIPE, signal_string, DOUBLE_PIPE))
			sample_index += 1
		channel_index += 1
	return ''.join(result_lines)



if __name__ == '__main__':
	main()
