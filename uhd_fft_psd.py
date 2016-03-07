#!/usr/bin/env python
#
# Copyright 2012 Free Software Foundation, Inc.
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

from gnuradio import gr, gru, blocks
from gnuradio import uhd
from gnuradio import eng_notation
from gnuradio.eng_option import eng_option
from optparse import OptionParser
from gnuradio import analog
from grc_gnuradio import blks2 as grc_blks2
import sys
import numpy
import time
import thread
import threading

try:
    from gnuradio.wxgui import stdgui2, form, slider
    from gnuradio.wxgui import forms
    from gnuradio.wxgui import fftsink2_, waterfallsink2, scopesink2
    import wx
except ImportError:
    sys.stderr.write("Error importing GNU Radio's wxgui. Please make sure gr-wxgui is installed.\n")
    sys.exit(1)

def restart(top):
    time.sleep(2)
    top.run()
    return True

class app_top_block(stdgui2.std_top_block):#stdgui2 comes from gr.top_block
    def __init__(self, frame, panel, vbox, argv):
        stdgui2.std_top_block.__init__(self, frame, panel, vbox, argv)

        self.frame = frame
        self.panel = panel

        parser = OptionParser(option_class=eng_option)
        parser.add_option("-a", "--args", type="string", default="",
                          help="UHD device address args , [default=%default]")
        parser.add_option("", "--spec", type="string", default=None,
                          help="Subdevice of UHD device where appropriate")
        parser.add_option("-A", "--antenna", type="string", default=None,
                          help="select Rx Antenna where appropriate")
        parser.add_option("-s", "--samp-rate", type="eng_float", default=1e6,
                          help="set sample rate (bandwidth) [default=%default]")
        parser.add_option("-f", "--freq", type="eng_float", default=None,
                          help="set frequency to FREQ", metavar="FREQ")
        parser.add_option("-g", "--gain", type="eng_float", default=None,
                          help="set gain in dB (default is midpoint)")
        parser.add_option("-W", "--waterfall", action="store_true", default=False,
                          help="Enable waterfall display")
        parser.add_option("-S", "--oscilloscope", action="store_true", default=False,
                          help="Enable oscilloscope display")
        parser.add_option("", "--avg-alpha", type="eng_float", default=1e-1,
                          help="Set fftsink averaging factor, default=[%default]")
        parser.add_option ("", "--averaging", action="store_true", default=False,
                           help="Enable fftsink averaging, default=[%default]")
        parser.add_option("", "--ref-scale", type="eng_float", default=1.0,
                          help="Set dBFS=0dB input value, default=[%default]")
        parser.add_option("", "--fft-size", type="int", default=1024,
                          help="Set number of FFT bins [default=%default]")
        parser.add_option("", "--fft-rate", type="int", default=30,
                          help="Set FFT update rate, [default=%default]")
        parser.add_option("", "--wire-format", type="string", default="sc16",
                          help="Set wire format from USRP [default=%default]")
        parser.add_option("", "--stream-args", type="string", default="",
                          help="Set additional stream args [default=%default]")
        parser.add_option("", "--show-async-msg", action="store_true", default=False,
                          help="Show asynchronous message notifications from UHD [default=%default]")
        parser.add_option("-b", "--bandwidth", type="eng_float", default=1e6,
                          help="set bandpass filter setting on the RF frontend")
        parser.add_option("-n", "--nsamples", type="eng_float", default=1024,
                          help="set number of samples which will be saved")
        parser.add_option("-N", "--samp-avg", type="eng_float", default=10,
                          help="set number of FFT samples which are averaged")
 
        (options, args) = parser.parse_args()
        if len(args) != 0:
            parser.print_help()
            sys.exit(1)
        self.options = options
        self.show_debug_info = True
	#Create USRP object
        self.u = uhd.usrp_source(device_addr=options.args,
                                 stream_args=uhd.stream_args(cpu_format='fc32',
                                 otw_format=options.wire_format, args=options.stream_args))


	#Create USRP object to transmit data to B200 (LO signal)
        self.u_lo = uhd.usrp_sink(
        	",".join(("", "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.u_lo.set_samp_rate(320000)
        self.u_lo.set_center_freq(25000000, 0)
        self.u_lo.set_gain(0, 0)


	# Create signal source
        self.sig_lo= analog.sig_source_c(320000, analog.GR_SIN_WAVE, 25000000, 0.316, 0)
	#(sample_rate, type, frequency, amplitude, offset)
	#Valve controls the streaming of LO
	self.valve = grc_blks2.valve(item_size=gr.sizeof_gr_complex*1, open=True)

	self.fft_size=options.fft_size


        # Set the subdevice spec
        if(options.spec):
            self.u.set_subdev_spec(options.spec, 0)

        # Set the antenna
        if(options.antenna):
            self.u.set_antenna(options.antenna, 0)
	# Set sample rate
        self.u.set_samp_rate(options.samp_rate)
        input_rate = self.u.get_samp_rate()

        # What kind of display will be shown
        if options.waterfall:
            self.scope = \
              waterfallsink2.waterfall_sink_c (panel, fft_size=1024,
                                               sample_rate=input_rate)
            self.frame.SetMinSize((800, 420))
	    
        elif options.oscilloscope:
            self.scope = scopesink2.scope_sink_c(panel, sample_rate=input_rate)
            self.frame.SetMinSize((800, 600))
	    
        else:
            self.scope = fftsink2_.fft_sink_c (panel,
                                              fft_size=options.fft_size,
                                              sample_rate=input_rate,
                          ref_scale=options.ref_scale,
                                              ref_level=20.0,
                                              y_divs = 12,
                                              average=options.averaging,
                          avg_alpha=options.avg_alpha,
                                              fft_rate=options.fft_rate)
	    
            def fftsink_callback(x, y):
                self.set_freq(x)

            self.scope.set_callback(fftsink_callback)
            self.frame.SetMinSize((800, 420))

        self.connect(self.u, self.scope)
	self.connect(self.sig_lo,self.valve, self.u_lo)

        self._build_gui(vbox)
        self._setup_events()


        # set initial values
	
	# Get gain
        if options.gain is None:
            # if no gain was specified, use the mid-point in dB
            g = self.u.get_gain_range()
            options.gain = float(g.start()+g.stop())/2

	#Get frequency
        if options.freq is None:
            # if no freq was specified, use the mid-point
            r = self.u.get_freq_range()#possible frequency range
            options.freq = float(r.start()+r.stop())/2#middle of the tunable frequency





	#Following lines must be after defining myform because set_freq, set_nsamples and set_gain need it
	
	# Set number of samples to store
	self.set_nsamples(options.nsamples)

        # Set bandwidth (passband filter on the RF frontend)
        self.set_bw(options.bandwidth)

	# Set gain
        self.set_gain(options.gain)

	# Set default LO frequency
	self.set_lo_freq(25000000)# LO frequency will be 25MHz, by default

   

        if self.show_debug_info:
            self.myform['samprate'].set_value(self.u.get_samp_rate())
            self.myform['rffreq'].set_value(0)
            self.myform['dspfreq'].set_value(0)

        if not(self.set_freq(options.freq)):
            self._set_status_msg("Failed to set initial frequency")
	else:
	    self.set_filename("Data_nsam_"+str(self.nsamp)+"_samprate_"+str(input_rate)+ "_bw_"+str(self.bandwidth)+"_cfreq_"+str(self.u.get_center_freq())+"_.txt")

        # Direct asynchronous notifications to callback function
        if self.options.show_async_msg:
            self.async_msgq = gr.msg_queue(0)
            self.async_src = uhd.amsg_source("", self.async_msgq)
            self.async_rcv = gru.msgq_runner(self.async_msgq, self.async_callback)

    def async_callback(self, msg):
        md = self.async_src.msg_to_async_metadata_t(msg)
        print "Channel: %i Time: %f Event: %i" % (md.channel, md.time_spec.get_real_secs(), md.event_code)

    def _set_status_msg(self, msg):
        self.frame.GetStatusBar().SetStatusText(msg, 0)



    # Build GUI, buttons part
    def _build_gui(self, vbox):

        def _form_set_freq(kv):
            return self.set_freq(kv['freq'])

        vbox.Add(self.scope.win, 10, wx.EXPAND)

        # add control area at the bottom
        self.myform = myform = form.form()
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add((5,0), 0, 0)
        myform['freq'] = form.float_field(
            parent=self.panel, sizer=hbox, label="Center freq", weight=1,
            callback=myform.check_input_and_call(_form_set_freq,
                                                 self._set_status_msg))

        hbox.Add((5,0), 0, 0)
        g = self.u.get_gain_range()

        # some configurations don't have gain control
        if g.stop() <= g.start():
            glow = 0.0
            ghigh = 1.0

        else:
            glow = g.start()
            ghigh = g.stop()

        myform['gain'] = form.slider_field(parent=self.panel,
                                               sizer=hbox, label="Gain",
                                               weight=3,
                                               min=int(glow), max=int(ghigh),
                                               callback=self.set_gain)

        try:
            mboard_id = self.u.get_usrp_info()["mboard_id"]
            mboard_serial = self.u.get_usrp_info()["mboard_serial"]
            if mboard_serial == "":
                mboard_serial = "no serial"
            dboard_subdev_name = self.u.get_usrp_info()["rx_subdev_name"]
            dboard_serial = self.u.get_usrp_info()["rx_serial"]
            if dboard_serial == "":
                dboard_serial = "no serial"
            subdev = self.u.get_subdev_spec()
            antenna = self.u.get_antenna()

            if "B200" in mboard_id or "B210" in mboard_id:
                usrp_config_val = "%s (%s), %s (%s, %s)" % (mboard_id, mboard_serial, dboard_subdev_name, subdev, antenna)
            else:
                usrp_config_val = "%s (%s), %s (%s, %s, %s)" % (mboard_id, mboard_serial, dboard_subdev_name, dboard_serial, subdev, antenna)
        except:
            usrp_config_val = "Not implemented in this version."

        uhd_box = forms.static_box_sizer(parent=self.panel,
                                         label="UHD (%s)" % (uhd.get_version_string()),
                                         orient=wx.HORIZONTAL)
        usrp_config_form = forms.static_text(
            parent=self.panel,
            sizer=uhd_box,
            value=usrp_config_val,
            label="USRP",
            converter=forms.str_converter(),
        )
        vbox.Add(uhd_box, 0, wx.EXPAND)
        vbox.AddSpacer(5)

        hbox.Add((5,0), 0, 0)
        vbox.Add(hbox, 0, wx.EXPAND)


	# Create subpanel 2
        self._build_subpanel(vbox)
        self._build_subpanel3(vbox)
        self._build_subpanel4(vbox)
        self._build_subpanel5(vbox)
      #End of first panel





    #Subpanel 2
    def _build_subpanel(self, vbox_arg):
        # build a secondary information panel (sometimes hidden)

        # FIXME figure out how to have this be a subpanel that is always
        # created, but has its visibility controlled by foo.Show(True/False)

        def _form_set_samp_rate(kv):
            return self.set_samp_rate(kv['samprate'])

        def _form_set_bandwidth(kv):
            return self.set_bw(kv['bandw'])

        if not(self.show_debug_info):
            return

        panel = self.panel
        vbox = vbox_arg
        myform = self.myform

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        hbox.Add((5,0), 0)
        myform['samprate'] = form.float_field(
            parent=panel, sizer=hbox, label="Sample Rate",
            callback=myform.check_input_and_call(_form_set_samp_rate,
                                                 self._set_status_msg))
        hbox.Add((5,0), 0)
	#Create box to receive saple rate value
        myform['bandw'] = form.float_field(
            parent=panel, sizer=hbox, label="Bandwidth",
            callback=myform.check_input_and_call(_form_set_bandwidth,
                                                 self._set_status_msg))

        hbox.Add((5,0), 1)
        myform['rffreq'] = form.static_float_field(
            parent=panel, sizer=hbox, label="RF Freq.")

        hbox.Add((5,0), 1)
        myform['dspfreq'] = form.static_float_field(
            parent=panel, sizer=hbox, label="DSP Freq.")

        vbox.AddSpacer(5)

        vbox.Add(hbox, 0, wx.EXPAND)
        vbox.AddSpacer(5)

    # End of subpanel 2




    # Subpanel 3
#!!!!!!!!!!!!!!!!!!!


    def _build_subpanel3(self, vbox_arg):

        panel = self.panel
        vbox = vbox_arg
        myform = self.myform

	def _form_set_nsamples(kv):
            return self.set_nsamples(kv['numsamp'])



 

	def _form_set_filename(kv):
            return self.set_filename(kv['fname'])

        hbox = wx.BoxSizer(wx.HORIZONTAL)
	hbox.Add((5,0), 0)
        myform['fname'] = form.text_field(
            parent=panel, sizer=hbox, label="Filename",
            callback=myform.check_input_and_call(_form_set_filename,
                                                 self._set_status_msg))
	hbox.Add((5,0), 0)
        myform['numsamp'] = form.float_field(
            parent=panel, sizer=hbox, label="Number of Samples",
            callback=myform.check_input_and_call(_form_set_nsamples,
                                                 self._set_status_msg))



        hbox.Add((10,0), 0)

	#Create a button to save data
        #myform['savefile'] = form.button_with_callback(parent=panel,      label="Save Data", callback=myform.check_input_and_call(self.set_gain))
        myform['savefile'] = form.checkbox_field(parent=panel,        label="Save Data", sizer=hbox, callback=self.save_data)
       
        

        vbox.AddSpacer(5)

        vbox.Add(hbox, 0, wx.EXPAND)
        vbox.AddSpacer(5)

	
#!!!!!!!!!!!!!!!!!!!

    # End subpanel 3







    # Subpanel 4
#!!!!!!!!!!!!!!!!!!!


    def _build_subpanel4(self, vbox_arg):

        panel = self.panel
        vbox = vbox_arg
        myform = self.myform

        hbox = wx.BoxSizer(wx.HORIZONTAL)


        hbox.Add((5,0), 0, 0)#Add space between the previous and next box, horizontally

        # Create a bar or slider horizontally, it is labeled "LO frequency" and it moves in the interval [20M,30M] Hz,once it is moved it calls back to the function set_lo_freq 
        myform['lofreq'] = form.slider_field(parent=self.panel,
                                               sizer=hbox, label="LO frequency (Hz)",
                                               weight=3,
                                               min=20000000, max=30000000,
                                               callback=self.set_lo_freq)
        hbox.Add((10,0), 0)

	#Create a checkbox to produce LO signal (the signal will go out when the box is ticked)
        myform['LO'] = form.checkbox_field(parent=panel,        label="LO generator", sizer=hbox, callback=self.begin_thread2)
       
        

        vbox.AddSpacer(5)

        vbox.Add(hbox, 0, wx.EXPAND)
        vbox.AddSpacer(5)

	
#!!!!!!!!!!!!!!!!!!!

    # End subpanel 4














    # Subpanel 5
#!!!!!!!!!!!!!!!!!!!


    def _build_subpanel5(self, vbox_arg):

        panel = self.panel
        vbox = vbox_arg
        myform = self.myform

        hbox = wx.BoxSizer(wx.HORIZONTAL)



        hbox.Add((10,0), 0)

	#Create a checkbox to produce LO signal (the signal will go out when the box is ticked)
        myform['inte'] = form.checkbox_field(parent=panel,        label="Begin integration", sizer=hbox, callback=self.integrate)
       
        

        vbox.AddSpacer(5)

        vbox.Add(hbox, 0, wx.EXPAND)
        vbox.AddSpacer(5)

	
#!!!!!!!!!!!!!!!!!!!

    # End subpanel 5









    # Define functions


    # In case of change parameters, change name
    def set_fname(self):
	self.set_filename("Data_nsam_"+str(self.nsamp)+"_samprate_"+str(self.u.get_samp_rate())+ "_bw_"+str(self.u.get_bandwidth())+"_cfreq_"+str(self.u.get_center_freq())+"_.txt")


    def set_nsamples(self,numb_samp):
	self.nsamp=numb_samp
	print self.nsamp
        if self.show_debug_info:  # update displayed values
            self.myform['numsamp'].set_value(self.nsamp)
            self.set_fname()
	return True



    def set_filename(self,name):
	self.filename=name
	#print self.filename
        if self.show_debug_info:  # update displayed values
            self.myform['fname'].set_value(self.filename)
        return True
    
    def set_bw(self,bdwh):
	a=self.u.set_bandwidth(bdwh)
        self.bandwidth=bdwh
        if self.show_debug_info:  # update displayed values
            self.myform['bandw'].set_value(self.u.get_bandwidth())
            self.set_fname()	
	return True



    def set_freq(self, target_freq):
        """
        Set the center frequency we're interested in.

        @param target_freq: frequency in Hz
        @rypte: bool
        """
        r = self.u.set_center_freq(target_freq, 0)

        if r:
            self.myform['freq'].set_value(self.u.get_center_freq())
            self.myform['rffreq'].set_value(r.actual_rf_freq)
            self.myform['dspfreq'].set_value(r.actual_dsp_freq)

            if not self.options.oscilloscope:
                self.scope.set_baseband_freq(target_freq)
            return True

        return False

    def set_gain(self, gain):
        if self.myform.has_key('gain'):
            self.myform['gain'].set_value(gain)     # update displayed value
        self.u.set_gain(gain, 0)

    def set_samp_rate(self, samp_rate):
        ok = self.u.set_samp_rate(samp_rate)
        input_rate = self.u.get_samp_rate()
        self.scope.set_sample_rate(input_rate)
        if self.show_debug_info:  # update displayed values
            self.myform['samprate'].set_value(self.u.get_samp_rate())

        # uhd set_samp_rate never fails; always falls back to closest requested.
        return True



    # Set LO frequency
    def set_lo_freq(self, lofreq):
        if self.myform.has_key('lofreq'):
            self.myform['lofreq'].set_value(lofreq)     # update displayed value
        self.sig_lo.set_frequency(lofreq) # Adjust gain to the USRP object

    #Thread 2 calls the LO genetrator
    def begin_thread2(self,ticket):
	 t = threading.Thread(target=self.LO_gen, args=(ticket,))#args must be a sequence

         t.start()
	 #t.join() deja tomado hasta que termina el thread

		
	
    def LO_gen(self,ticket):
	if ticket: #only produce data whet the box is checked
		print "producing LO"
		self.valve.set_open(False) 

	else:
		#self.stop()		
		#self.wait()
		print "disconnect LO "
		self.valve.set_open(True) 
		



    #Thread 2 calls the LO genetrator
    def integrate(self,ticket):
	if ticket:
	    if ((not (self.options.waterfall) ) and (not(self.options.oscilloscope))):
		##self.scope.operate_valve(1) #chose ports 1
		#self.connect(self.scope.integrate, self.scope.file_sink_int)
		#self.fft_=self.scope.get_fft() #chose ports 1
	 	# For saving data (integration)
		#int_filename="integration_data3.txt"
		#print "create blocks"
		#self.vect2str= blocks.vector_to_stream(gr.sizeof_float*1, self.fft_size)
       	        #self.integrate = blocks.integrate_ff(self.fft_size, 1)
        	#self.file_sink_int= blocks.file_sink(gr.sizeof_float*1, int_filename, False)
		#self.connect(self.fft_, self.vect2str, self.integrate, self.file_sink_int) 
		print "No hace nada :c "

	    else:
		print "To integrate data please use FFT display mode"

	else:
		#self.scope.operate_valve(0) #chose ports 0
		#self.null_sink = blocks.null_sink(gr.sizeof_float*1)	
		#self.connect(self.integrate, self.null_sink)#for nopt leaving nothing disconnected
		#self.disconnect(self.integrate, self.file_sink_int)
		print "disconnect"


	    


    def save_data(self,nada):
	if nada:#Save data only when you check the box (not when you un-check it)
		#Create file to receive data
		self._sink=blocks.file_sink(gr.sizeof_gr_complex,str(self.filename))
	#Crear bloque que contenga las muestras (head block)
		print "real nsamp "+ str(int(self.nsamp))
		self._head=blocks.head(gr.sizeof_gr_complex,int(self.nsamp/2))
                self.stop()
                #print "C1"
		self.wait()
                #print "C2"
	#Conectar tarjeta con la cantidad de muestras y el archivo
                #self.disconnect(self.u)
		self.disconnect_all()
                #self.connect(self.u,self.scope)
                self.connect(self.u,self._head,self._sink)
                a=thread.start_new_thread(restart, (self,))
		#print "a: "+ str(a)
		time.sleep(4)
                self.stop()
                #print "D1"
		self.wait()
                #print "D2"
	#Conectar tarjeta con la cantidad de muestras y el archivo
                #self.disconnect(self.u)
                self.disconnect_all()
		self.connect(self.u,self.scope)
                thread.start_new_thread(restart, (self,))
                #print "D3"
                #print "C3"
		#print "1"
		#self.run()
		#print "2"
		#self.save=SaveData(self.nsamp,self.filename,self.u)
		#self.save.run(10)
		#self.con=Reconnect(self.u,self.scope)
                #self.con.run(10)
	        '''
           SaveData(self.nsamp,self.filename,self.u).start()
	   SaveData(self.nsamp,self.filename,self.u).stop()
	   SaveData(self.nsamp,self.filename,self.u).wait()
            self.save=SaveData(self.nsamp,self.filename,self.u)
          # self.save.run()
	 #  self.connect(self.u, self.scope)#reconnect source board (u) with display  
          # self.save.wait()
           #self.save.stop()
	   self.con=Reconnect(self.u,self.scope)
           self.con.start()
               '''
               
        else:
		a=1
                ''' self.stop()
                print "D1"
		self.wait()
                print "D2"
	#Conectar tarjeta con la cantidad de muestras y el archivo
                #self.disconnect(self.u)
                self.disconnect_all()
		self.connect(self.u,self.scope)
                thread.start_new_thread(restart, (self,))
                print "D3"

                '''




    def _setup_events(self):
        if not self.options.waterfall and not self.options.oscilloscope:
            self.scope.win.Bind(wx.EVT_LEFT_DCLICK, self.evt_left_dclick)

    def evt_left_dclick(self, event):
        (ux, uy) = self.scope.win.GetXY(event)
        if event.CmdDown():
            # Re-center on maximum power
            points = self.scope.win._points
            if self.scope.win.peak_hold:
                if self.scope.win.peak_vals is not None:
                    ind = numpy.argmax(self.scope.win.peak_vals)
                else:
                    ind = int(points.shape()[0]/2)
            else:
                ind = numpy.argmax(points[:,1])

            (freq, pwr) = points[ind]
            target_freq = freq/self.scope.win._scale_factor
            print ind, freq, pwr
            self.set_freq(target_freq)
        else:
            # Re-center on clicked frequency
            target_freq = ux/self.scope.win._scale_factor
            self.set_freq(target_freq)


def main ():
    try:
        app = stdgui2.stdapp(app_top_block, "UHD FFT", nstatus=1)
        app.MainLoop()

    except RuntimeError, e:
        print e
        sys.exit(1)

if __name__ == '__main__':
    main ()