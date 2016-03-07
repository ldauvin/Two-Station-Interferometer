#
# Copyright 2008 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#


# USA ESTE ARCHIVO
#print "Pasando por aqui"
#This block only computes fft, its square of module and average 30 samples of it, logarithm is computed outside this block in order to save data without that calculation (log only helps to show data in GUI)
from gnuradio import gr
from gnuradio import blocks
import sys, math

import fft_swig as fft
from fft_swig import window

try:
    from gnuradio import filter
except ImportError:
    sys.stderr.write('fft.logpwrfft required gr-filter.\n')
    sys.exit(1)

class _logpwrfft_base(gr.hier_block2):
    """
    Create a log10(abs(fft)) stream chain, with real or complex input.
    """

    def __init__(self, sample_rate, fft_size, ref_scale, frame_rate, avg_alpha, average, win=None):
        """
        Create an log10(abs(fft)) stream chain.
        Provide access to the setting the filter and sample rate.

        Args:
            sample_rate: Incoming stream sample rate
            fft_size: Number of FFT bins
            ref_scale: Sets 0 dB value input amplitude
            frame_rate: Output frame rate
            avg_alpha: FFT averaging (over time) constant [0.0-1.0]
            average: Whether to average [True, False]
            win: the window taps generation function
        """
        gr.hier_block2.__init__(self, self._name,
                                gr.io_signature(1, 1, self._item_size),          # Input signature
                                gr.io_signature(1, 1, gr.sizeof_float*fft_size)) # Output signature

        self._sd = blocks.stream_to_vector_decimator(item_size=self._item_size,
                                                     sample_rate=sample_rate,
                                                     vec_rate=frame_rate,
                                                     vec_len=fft_size)

        if win is None: win = window.blackmanharris
        fft_window = win(fft_size)
        fft = self._fft_block[0](fft_size, True, fft_window)
        window_power = sum(map(lambda x: x*x, fft_window))

        c2magsq = blocks.complex_to_mag_squared(fft_size)
        self._avg = filter.single_pole_iir_filter_ff(1.0, fft_size)

	# Computes the average
	# Separate stream into 30 samples
	self.deint= blocks.deinterleave(gr.sizeof_float*fft_size, 1)#vector length, blocks size=1, since we need to separate in blocks of 1 vector of 1024 samples (is fft_size=1024)
	
	#Add the 30 new streams
        self.add = blocks.add_vff(fft_size)#floats in, floats out, vector of fft_zise elements	

	# Divide in 30= multiply *(1/30)
	self.factor=1.0/30.0
	self.divide= blocks.multiply_const_vff((fft_size*[self.factor]))#float in, floats out, divide in a vector of length fft_size and values of self.factor




		




	# Logarithm is only needed to show the result in the GUI
        self._log = blocks.nlog10_ff(10, fft_size,
                                     -20*math.log10(fft_size)              # Adjust for number of bins
                                     -10*math.log10(window_power/fft_size) # Adjust for windowing loss
                                     -20*math.log10(ref_scale/2))      # Adjust for reference scale

	#vector to str
	#self.dst=blocks.vector_sink_f()

        self.connect(self, self._sd, fft, c2magsq, self.deint)
	#self.connect(self._log, self.dst)

	#Connects blocks which are an average. We should have 30 ports
	for i in range (0,29):
             self.connect((self.deint, i), (self.add, i)) 

	# Divide in 30
	self.connect(self.add , self)
	#self.connect(self.add ,self._log, self)








        self._average = average
        self._avg_alpha = avg_alpha
        self.set_avg_alpha(avg_alpha)
        self.set_average(average)


	#result_data = dst.data()
	#print str(result_data)


    def set_decimation(self, decim):
        """
        Set the decimation on stream decimator.

        Args:
            decim: the new decimation
        """
        self._sd.set_decimation(decim)

    def set_vec_rate(self, vec_rate):
        """
        Set the vector rate on stream decimator.

        Args:
            vec_rate: the new vector rate
        """
        self._sd.set_vec_rate(vec_rate)

    def set_sample_rate(self, sample_rate):
        """
        Set the new sampling rate

        Args:
            sample_rate: the new rate
        """
        self._sd.set_sample_rate(sample_rate)

    def set_average(self, average):
        """
        Set the averaging filter on/off.

        Args:
            average: true to set averaging on
        """
        self._average = average
        if self._average:
            self._avg.set_taps(self._avg_alpha)
        else:
            self._avg.set_taps(1.0)

    def set_avg_alpha(self, avg_alpha):
        """
        Set the average alpha and set the taps if average was on.

        Args:
            avg_alpha: the new iir filter tap
        """
        self._avg_alpha = avg_alpha
        self.set_average(self._average)

    def sample_rate(self):
        """
        Return the current sample rate.
        """
        return self._sd.sample_rate()

    def decimation(self):
        """
        Return the current decimation.
        """
        return self._sd.decimation()

    def frame_rate(self):
        """
        Return the current frame rate.
        """
        return self._sd.frame_rate()

    def average(self):
        """
        Return whether or not averaging is being performed.
        """
        return self._average

    def avg_alpha(self):
        """
        Return averaging filter constant.
        """
        return self._avg_alpha
    # Returns the log block...is not a beauty way to do it, but it works; hence, we don't have to redefine parameters in an other block, since they are the same (such as "window"or "window power")
    def get_log(self):
	'''
	Return the log block
	'''
	return self._log

class logpwrfft_f(_logpwrfft_base):
        """
        Create an fft block chain, with real input.
        """
        _name = "logpwrfft_f"
        _item_size = gr.sizeof_float
        _fft_block = (fft.fft_vfc, )

class logpwrfft_c(_logpwrfft_base):
        """
        Create an fft block chain, with complex input.
        """
        _name = "logpwrfft_c"
        _item_size = gr.sizeof_gr_complex
        _fft_block = (fft.fft_vcc, )
