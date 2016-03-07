#
# Copyright 2008-2010,2012 Free Software Foundation, Inc.
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

# SE USA ESTE ARCHIVO

from __future__ import division

##################################################
# Imports
##################################################
import fft_window
import common
from gnuradio import gr, fft
from gnuradio import analog
from gnuradio import blocks
from gnuradio.fft import logpwrfft
from pubsub import pubsub
from constants import *
from grc_gnuradio import blks2 as grc_blks2
import math
import scipy



##################################################
# FFT sink block (wrapper for old wxgui)
##################################################
class _fft_sink_base(gr.hier_block2, common.wxgui_hb):
	"""
	An fft block with real/complex inputs and a gui window.
	"""

	def __init__(
		self,
		parent,
		baseband_freq=0,
		ref_scale=2.0,
		y_per_div=10,
		y_divs=8,
		ref_level=50,
		sample_rate=1,
		fft_size=512,
		fft_rate=fft_window.DEFAULT_FRAME_RATE,
		average=False,
		avg_alpha=None,
		title='',
		size=fft_window.DEFAULT_WIN_SIZE,
		peak_hold=False,
		win=None,
                use_persistence=False,
                persist_alpha=None,
		**kwargs #do not end with a comma
	):
		#ensure avg alpha
		if avg_alpha is None: avg_alpha = 2.0/fft_rate
                #ensure analog alpha
                if persist_alpha is None:
                  actual_fft_rate=float(sample_rate/fft_size)/float(max(1,int(float((sample_rate/fft_size)/fft_rate))))
                  #print "requested_fft_rate ",fft_rate
                  #print "actual_fft_rate    ",actual_fft_rate
                  analog_cutoff_freq=0.5 # Hertz
                  #calculate alpha from wanted cutoff freq
                  persist_alpha = 1.0 - math.exp(-2.0*math.pi*analog_cutoff_freq/actual_fft_rate)

		#init
		gr.hier_block2.__init__(
			self,
			"fft_sink",
			gr.io_signature(1, 1, self._item_size),
			gr.io_signature(0, 0, 0),
		)


       	        self.integrating = integrating = 0


		#blocks
		self.fft = self._fft_chain(
			sample_rate=sample_rate,
			fft_size=fft_size,
			frame_rate=fft_rate,
			ref_scale=ref_scale,
			avg_alpha=avg_alpha,
			average=average,
			win=win,
		)
		msgq = gr.msg_queue(2)
		sink = blocks.message_sink(gr.sizeof_float*fft_size, msgq, True)
		# For graphical display only
		self._log=self.fft.get_log()

		# For saving data (integration)
		int_filename="integration_data2.txt"

		self.vect2str= blocks.vector_to_stream(gr.sizeof_float*1, fft_size)
       	        self.integrate = blocks.integrate_ff(fft_size, 1)
        	self.file_sink_int= blocks.file_sink(gr.sizeof_float*1, int_filename, False)
		#controls data streaming
		#self.integrating=1 #if the valve is open (1) or closed (0). Open valve stops data
		#self._valve = grc_blks2.valve(item_size=gr.sizeof_float*1, open=bool(self.integrating))

      	     #   self.selec = grc_blks2.selector(
        	#item_size=gr.sizeof_float*1,
      #  	num_inputs=2,
       # 	num_outputs=2,
        #	input_index=integrating,
        #	output_index=integrating,
        #)
	
		#just for not leave ports disconnected
       	        #self.null_source = blocks.null_source(gr.sizeof_float*1)
       	        #self.null_sink = blocks.null_sink(gr.sizeof_float*1)	

		#controller
		self.controller = pubsub()
		self.controller.subscribe(AVERAGE_KEY, self.fft.set_average)
		self.controller.publish(AVERAGE_KEY, self.fft.average)
		self.controller.subscribe(AVG_ALPHA_KEY, self.fft.set_avg_alpha)
		self.controller.publish(AVG_ALPHA_KEY, self.fft.avg_alpha)
		self.controller.subscribe(SAMPLE_RATE_KEY, self.fft.set_sample_rate)
		self.controller.publish(SAMPLE_RATE_KEY, self.fft.sample_rate)
		#start input watcher
		common.input_watcher(msgq, self.controller, MSG_KEY)
		#create window
		self.win = fft_window.fft_window(
			parent=parent,
			controller=self.controller,
			size=size,
			title=title,
			real=self._real,
			fft_size=fft_size,
			baseband_freq=baseband_freq,
			sample_rate_key=SAMPLE_RATE_KEY,
			y_per_div=y_per_div,
			y_divs=y_divs,
			ref_level=ref_level,
			average_key=AVERAGE_KEY,
			avg_alpha_key=AVG_ALPHA_KEY,
			peak_hold=peak_hold,
			msg_key=MSG_KEY,
                        use_persistence=use_persistence,
                        persist_alpha=persist_alpha,
		)
		common.register_access_methods(self, self.win)
		setattr(self.win, 'set_baseband_freq', getattr(self, 'set_baseband_freq')) #BACKWARDS
		setattr(self.win, 'set_peak_hold', getattr(self, 'set_peak_hold')) #BACKWARDS
		#connect
		self.wxgui_connect(self,self.fft, self._log, sink)# GUI
		#Save data
		#self.connect(self.null_source,(self.selec,0))#selector is in ports 0 by default
		#self.connect((self.selec,0),self.null_sink)
		#self.connect(self.fft, self.vect2str, self.integrate, (self.selec,1)) #port 1 os select is to save data
                #self.connect((self.selec,1), self.file_sink_int)#SAVE DATA
		self.connect(self.fft, self.vect2str, self.integrate, self.file_sink_int) 
		




	def set_callback(self,callb):
		self.win.set_callback(callb)
	'''
	def operate_valve(self, integrating):
		self.integrating=integrating
		print "Operating ports > " + str(self.integrating) 
       	        self.selec.set_input_index(int(self.integrating))
        	self.selec.set_output_index(int(self.integrating))
	'''
	def get_fft(self):
		return self.fft
		


class fft_sink_f(_fft_sink_base):
	_fft_chain = logpwrfft.logpwrfft_f
	_item_size = gr.sizeof_float
	_real = True

class fft_sink_c(_fft_sink_base):
	_fft_chain = logpwrfft.logpwrfft_c
	_item_size = gr.sizeof_gr_complex
	_real = False
	#get_fft()

# ----------------------------------------------------------------
# Standalone test app
# ----------------------------------------------------------------

import wx
from gnuradio.wxgui import stdgui2

class test_app_block (stdgui2.std_top_block):
    def __init__(self, frame, panel, vbox, argv):
        stdgui2.std_top_block.__init__(self, frame, panel, vbox, argv)

        fft_size = 256

        # build our flow graph
        input_rate = 2048.0e3

        #Generate some noise
        noise = analog.noise_source_c(analog.GR_UNIFORM, 1.0/10)

        # Generate a complex sinusoid
        #src1 = analog.sig_source_c(input_rate, analog.GR_SIN_WAVE, 2e3, 1)
        src1 = analog.sig_source_c(input_rate, analog.GR_CONST_WAVE, 57.50e3, 1)

        # We add these throttle blocks so that this demo doesn't
        # suck down all the CPU available.  Normally you wouldn't use these.
        thr1 = blocks.throttle(gr.sizeof_gr_complex, input_rate)

        sink1 = fft_sink_c(panel, title="Complex Data", fft_size=fft_size,
			   sample_rate=input_rate, baseband_freq=100e3,
			   ref_level=0, y_per_div=20, y_divs=10)
        vbox.Add(sink1.win, 1, wx.EXPAND)

        combine1 = blocks.add_cc()
        self.connect(src1, (combine1,0))
        self.connect(noise,(combine1,1))
        self.connect(combine1,thr1, sink1)

        #src2 = analog.sig_source_f(input_rate, analog.GR_SIN_WAVE, 2e3, 1)
        src2 = analog.sig_source_f (input_rate, analog.GR_CONST_WAVE, 57.50e3, 1)
        thr2 = blocks.throttle(gr.sizeof_float, input_rate)
        sink2 = fft_sink_f(panel, title="Real Data", fft_size=fft_size*2,
			   sample_rate=input_rate, baseband_freq=100e3,
			   ref_level=0, y_per_div=20, y_divs=10)
        vbox.Add(sink2.win, 1, wx.EXPAND)

        combine2 = blocks.add_ff()
        c2f2 = blocks.complex_to_float()

        self.connect(src2, (combine2,0))
        self.connect(noise,c2f2,(combine2,1))
        self.connect(combine2, thr2,sink2)

def main ():
    app = stdgui2.stdapp(test_app_block, "FFT Sink Test App")
    app.MainLoop()

if __name__ == '__main__':
    main()