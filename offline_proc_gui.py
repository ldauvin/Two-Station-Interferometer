#!/usr/bin/python
# -*- coding: utf-8 -*-
#Importar librerias
from Tkinter import *
from Tkinter import Tk, BOTH
from ttk import Frame, Button, Style
from tkFileDialog import askopenfilename
import struct
import matplotlib.pyplot as plt
import math
import time
from numpy import *
from pylab import plot, ginput, show, axis
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Funcion que recopila los datos del archivo binario de GNU radio
# El codigo de GNU Radio produce floats, por lo tanto es el formato que se lee
def myplotcode(filename):
    floats = []
    with open(filename, "rb") as f:
        word = f.read(4)
        while word != "":
            floats.append(struct.unpack('f', word)[0])
            word = f.read(4)
    return floats


#Clase que genera la interfaz
class gui(Frame):
  
    def __init__(self, parent):
        Frame.__init__(self, parent)   
         
        self.parent = parent
        self.initUI()
        
        
    def initUI(self):
      
        self.parent.title("Sun diameter calculator")#titulo
        self.style = Style()
        self.style.theme_use("default")

        self.pack(fill=BOTH, expand=1)
	#Boton que abre archivo
        quitButton = Button(self,text="Open file",
            command=self.openfile)
        quitButton.place(x=50, y=50)
	
	#Mostar imagen de referencia
	canvas = Canvas(self,width = 544, height = 363, bg = 'white')
	canvas.pack(expand = YES, fill = BOTH)
	#Abrir la imagen, que debe estar en el mismo directorio
	self.gif1 = PhotoImage(file = 'grafica.png')
	canvas.create_image(0, 0, image = self.gif1,anchor=NW)
	canvas.place(x=400, y=50)

	#Boton para iniciar el proceso de adquirir puntos, es decir, el de maxima y minima potencia, y dos puntos que marquen el periodo de la senal sinusoidal
        corrButton = Button(self, text="Click to input points",
            command=self.corre)
        corrButton.place(x=50, y=550)
        
	# Una vez seteados los parametros, apretar este boton para definir los parametros
        compButton = Button(self, text="Set Parameters and plot data",
            command=self.setP)
        compButton.place(x=150, y=50)

	# Boton para realizar el calculo
        calButton = Button(self, text="Compute",
            command=self.calculate)
        calButton.place(x=250, y=550)

	 
	# Mensaje de instrucciones
	self.w = Message(self, text="Open file", width=1000)
	self.w.pack()
	self.w.place(x=50, y=700)

	# Mensaje que muestra los puntos que se escogieron
	self.w2 = Message(self, text="", width=1000)
	self.w2.pack()
	self.w2.place(x=50, y=600)

	#Mensaje que muestra los resultados del calculo
	self.txt2= "RESULTS: \n\n"
	self.w3 = Message(self, text=self.txt2, width=1000)
	self.w3.pack()
	self.w3.place(x=450, y=450)

	# Boolean que determina cuando se debe iniciar la captura de puntos
	self.correct=False

	#Espacios para parametros
	L1 = Label(self, text="Sample rate: ")
	L1.pack( side = LEFT)
	L1.place(x=50, y=100)
	self.E1 = Entry(self, bd =5)
	self.E1.pack(side = RIGHT)
	self.E1.place(x=200, y=100)

	L2 = Label(self, text="Bandwidth [Hz]: ")
	L2.pack( side = LEFT)
	L2.place(x=50, y=150)
	self.E2 = Entry(self, bd =5)
	self.E2.pack(side = RIGHT)
	self.E2.place(x=200, y=150)

	L3 = Label(self, text="Center frequency [Hz]: ")
	L3.pack( side = LEFT)
	L3.place(x=50, y=200)
	self.E3 = Entry(self, bd =5)
	self.E3.pack(side = RIGHT)
	self.E3.place(x=200, y=200)

	L4 = Label(self, text="Measured baseline [m]: ")
	L4.pack( side = LEFT)
	L4.place(x=50, y=250)
	self.E4 = Entry(self, bd =5)
	self.E4.pack(side = RIGHT)
	self.E4.place(x=200, y=250) 


	L5 = Label(self, text="Declination [deg]: ")
	L5.pack( side = LEFT)
	L5.place(x=50, y=300)
	self.E5 = Entry(self, bd =5)
	self.E5.pack(side = RIGHT)
	self.E5.place(x=200, y=300)

	L6 = Label(self, text="Sky frequency [Hz]: ")
	L6.pack( side = LEFT)
	L6.place(x=50, y=350)
	self.E6 = Entry(self, bd =5)
	self.E6.pack(side = RIGHT)
	self.E6.place(x=200, y=350)


	L7 = Label(self, text="fft size [samples]: ")
	L7.pack( side = LEFT)
	L7.place(x=50, y=400)
	self.E7 = Entry(self, bd =5)
	self.E7.pack(side = RIGHT)
	self.E7.place(x=200, y=400)

	L8 = Label(self, text="fft rate [samples]: ")
	L8.pack( side = LEFT)
	L8.place(x=50, y=450)
	self.E8 = Entry(self, bd =5)
	self.E8.pack(side = RIGHT)
	self.E8.place(x=200, y=450)

	L9 = Label(self, text="Start time [hh:mm]: ")
	L9.pack( side = LEFT)
	L9.place(x=50, y=500)
	self.E9 = Entry(self, bd =5)
	self.E9.pack(side = RIGHT)
	self.E9.place(x=200, y=500)

	self.opened=False #Boolean qye determina si se ha abierto un archivo con datos
	self.pset=False #Boolean que determina si se han seteado los datos
	self.cont=0
	plt.show()

    #Abrir archivo
    def openfile(self):
	self.filename=askopenfilename()
	#self.cont=self.cont+1
	self. txt=""
	self.opened=True
	self.w.config(text='Set parameters')

    # Comenzar captura cde puntos
    def corre(self):
	self.correct=True
	self.w.config(text='Click in maximum power')	

    #Graficar los datos segun los parametros
    def plotData(self):
	if self.opened:
		#se abrio el archivo
		if self.cont>0 :
			plt.close("all")
		#Grafico
		plt.figure()
		plt.plot(self.time1[20:len(self.floats)-1]/3600, self.floats[20:len(self.floats)-1])
		plt.ylabel('PSD [mW]')
		plt.xlabel('time [h]')
		plt.title('PSD')
		self.w.config(text='Press button to input points')
		b= False
		while (not b):
			# Recibir puntos
			pts_max = plt.ginput(1) 
        	        x_max=map(lambda x: x[0],pts_max) # map applies the function passed as 
		        y_max=map(lambda x: x[1],pts_max) # first parameter to each element of pts
			self.Pmax=y_max[0]

			b=self.correct
			time.sleep(1)

		self.txt= 'P max: ' +str(self.Pmax) + ' mW\n'
		self.w2.config(text=self.txt)
        	self.correct=False
	else:
		print "Escoja archivo" #porque aun no se abre archivo




	self.w.config(text='Click in minimum power')
	pts_min = ginput(1) 
	x_min=map(lambda x: x[0],pts_min) # map applies the function passed as 
	y_min=map(lambda x: x[1],pts_min) # first parameter to each element of pts
	self.Pmin=y_min[0]
	self.txt= self.txt + 'P min: ' +str(self.Pmin) + ' mW\n'
	self.w2.config(text=self.txt)

	#Lo mismo para obtener el periodo
        self.w.config(text='Click to get period: point 1')
	pts_v1 = ginput(1) 


	x_v1=map(lambda x: x[0],pts_v1) # map applies the function passed as 
	y_v1=map(lambda x: x[1],pts_v1) # first parameter to each element of pts
	d1= x_v1[0]

	self.w.config(text='Click to get period: point 2')
	pts_v2 = ginput(1) 

	x_v2=map(lambda x: x[0],pts_v2) # map applies the function passed as 
	y_v2=map(lambda x: x[1],pts_v2) # first parameter to each element of pts
	d2=x_v2[0]

	self.dis_peaks=(abs(d1-d2))*3600#secs
	self.txt= self.txt + 'Period: ' +str(self.dis_peaks) + ' seconds\n'
	self.w2.config(text=self.txt)

	plt.draw()
	
	self.cont=self.cont +1# Con el fin de saber cuantos archivos se han abierto
	self.w.config(text='Press compute button')

    # Setear parametros
    def setP(self): 

	self.samp_rate=float(self.E1.get())
	self.BW=float(self.E2.get())
	self.center_freq=float(self.E3.get())
	self.B=float(self.E4.get())
	self.dec_deg=float(self.E5.get())
	self.freq=float(self.E6.get())
	self.fft_size=float(self.E7.get())
	self.fft_rate=float(self.E8.get())
	timestr=self.E9.get() #hh:mm
	self.start=float(timestr[0:2])*3600.0+float(timestr[3:5])*60.0

	if self.opened:
		#Get data
		self.floats= myplotcode(self.filename)

		#Get time
		rate=1.0/0.96#(samp_rate/fft_rate/30/fft_size)#cantidad de datos por segundos
		print "Number of samples per second: " + str(rate)
		time_step=1.0/(rate) #segundos
		print "Time for each sample (sec): " + str(time_step)
		stop=time_step*len(self.floats)+self.start
		print self.start
		print stop
		print "Time step "+ str(time_step)
		self.time1=arange(self.start,stop,time_step)#start, stop, step
		#print str(len(time1))
		print "Length of vector time: "+ str(len(self.time1))
		print "Length of vector samples: "+ str(len(self.floats))
		print "Acquisition time: "+ str(((self.time1[len(self.floats)-1])-(self.time1[0]))/3600) + " horas"
		self.pset=True# Ahora que se tiene el eje tiempo, graficar
		self.plotData()
	else: 
		"Please open a file"
	


    # Determina el diametro del sol	
    def calculate(self):
	self.txt2="RESULTS: \n\n"
	c= 3.0e8# Velocidad de la luz [m/s]
	wv= c/self.freq #Longitud de onda [m] 
	dec= self.dec_deg*pi/180 #rad
	Bl_= self.B/wv #Bsublambda = B/ lambda
	lB_=1/Bl_ #distancia entre peaks

	#SD= diametro del sol
	# Expansion de Taylor de la funcion sinc
	# SD*(1-(((pi*Bl*SD)^2)/6))

	sun_v=2*pi/(24.0*3600.0)* cos(dec)  #velocidad angular del sol [rad/seg]. Da 2pi rad en 24 hrs es la maxima
	print "Sun velocity: "+str(sun_v)+ " [rad/seg]"
	rads=array(self.time1)*sun_v# transformacion de tiempo a grados, segun la velocidad del sol
	#print str(max(rads))
	dis_ang_peaks=self.dis_peaks*sun_v #distancia entre peaks en radianes
	#Luego distancia entre peaks= longitud de onda/ Baseline
	lB=dis_ang_peaks
	Bl=1/lB

	self.txt2= self.txt2 + "Calculated baseline: " +str(wv*Bl) + " [m]\n"
	self.txt2= self.txt2 + "Measured baseline: " + str(self.B) + " [m]\n"

	Visibilidad=(self.Pmax-self.Pmin)/(self.Pmax+self.Pmin)
	self.txt2= self.txt2 + "Visibility: " + str(Visibilidad) + "\n"

	SD= (math.sqrt(6)/pi)*(lB)*(math.sqrt(1-Visibilidad))#Con baseline calculada de los datos
	SD_= (math.sqrt(6)/pi)*(lB_)*(math.sqrt(1-Visibilidad))#Con baseline medida
	self.txt2= self.txt2 +"Sun diameter using calculated baseline: " + str(SD)+ " [rad]" + "\n"	
	self.txt2= self.txt2 + "Sun diameter using measured baseline: " + str(SD_)+ " [rad]" + "\n"
	
	# Transformar a arcmin
	sd_deg=SD*360/(2*pi)#deg
	sd_deg_=SD_*360/(2*pi)#deg
	self.txt2= self.txt2 + "Sun diameter using calculated baseline: " + str(sd_deg)+ " [deg]" + "\n"
	self.txt2= self.txt2 + "Sun diameter using measured baseline: " + str(sd_deg_)+ " [deg]" + "\n"

	sd_deg_norm=sd_deg-((int(sd_deg)/int(360))*360)#quitar revoluciones enteras extra
	sd_armin=sd_deg_norm*60 # arcmin
	self.txt2= self.txt2 +  "Sun diameter using calculated baseline: " + str(sd_armin)+ " [arcmin]" + "\n"
	
	self.w3.config(text=self.txt2)#Mostrar resultados en pantalla
	self.w.config(text='Open file to calculate again')

def main():
  
    root = Tk()
    root.geometry("960x750+300+300")# Tamano GUI
    app = gui(root)
    root.mainloop()  


if __name__ == '__main__':
    main() 
