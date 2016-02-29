#Offline data processing


import struct
import matplotlib.pyplot as plt
import numpy as np
import math
import time
from numpy import *
from pylab import plot, ginput, show, axis





def mysinc(x,a):
    y = []              # creates an empty list to store results
    for xx in x:        # loops over all elements in x array
        xx=xx*a
        if xx==0.0:     # adds result of 1.0 to y list if
            y += [1.0]  # xx is zero
        else:           # adds result of sin(xx)/xx to y list if
            y += [np.sin(xx)/xx]  # xx is not zero
    return np.array(y)  # converts y to array and returns array

def myrect(x,a):        #a es el ancho del rect
    y = []              # creates an empty list to store results
    for xx in x:        # loops over all elements in x array
        if abs(xx)<=a:     # adds result of 1.0 to y list if
            y += [1.0]  # xx is zero
        else:           # adds result of sin(xx)/xx to y list if
            y += [0]  # xx is not zero
    return np.array(y)  # converts y to array and returns array

def mymult(x,z):        #a es el ancho del rect
    y = [0]*len(x)              # creates an empty list to store results
    for i in range(0,len(x)-1):        # loops over all elements in x array
        y[i] = x[i]*z[i] # xx is zero
    print i
    return np.array(y)  # converts y to array and returns array




def myfilt(x,a,z):        #a es el ancho del rect
    y = []              # creates an empty list to store results
    cont=0
    for xx in x:        # loops over all elements in x array
        if cont<=a:     # adds result of 1.0 to y list if
            y += [z[cont]]  # xx is zero
        else:           # adds result of sin(xx)/xx to y list if
            y += [0]  # xx is not zero
        cont=cont+1
    return np.array(y)  # converts y to array and returns array




#Parametros


#'''
# Medicion 1
#Por el usuario
B= 0.428 #Baseline [m]
freq=11e9 # Frecuencia del cielo
dec_deg=-12.27 #deg
samp_rate=1e6
fft_size=1024
fft_rate=30
start=10*3600+(30*60) #inicio de medicion a las 12:27. hora de inicio de la medicion, en segundos
filename='20160218_data.txt'

#'''

'''
# Medicion 2
#Por el usuario
B= 1.483 #Baseline [m]
freq=11e9 # Frecuencia del cielo
dec_deg=-12.27 #deg
samp_rate=32e6
fft_size=1024
fft_rate=30
start=10*3600+(30*60) #inicio de medicion a las 12:27. hora de inicio de la medicion, en segundos
filename='20160222_data.txt'
'''



'''
# Medicion 3
#Por el usuario
B= 1.483 #Baseline [m]
freq=11e9 # Frecuencia del cielo
dec_deg=-12.27 #deg
samp_rate=6e6
fft_size=1024
fft_rate=30
start=12*3600+(27*60) #inicio de medicion a las 12:27. hora de inicio de la medicion, en segundos
filename='20160223_data.txt'
'''




'''
# Medicion 4
#Por el usuario
B= 1.483 #Baseline [m]
freq=11e9 # Frecuencia del cielo
dec_deg=-12.27 #deg
samp_rate=5e6
fft_size=1024
fft_rate=30
start=15*3600+(00*60) #inicio de medicion a las 12:27. hora de inicio de la medicion, en segundos
filename='20160223_data2.txt'
'''


'''
#Medicion 5
#Por el usuario
B= 1.483 #Baseline [m]
freq=11e9 # Frecuencia del cielo
dec_deg=-12.27 #deg
samp_rate=6e6
fft_size=1024
fft_rate=30
start=16*3600+(22*60) # hora de inicio de la medicion, en segundos
filename='20160223_data3.txt'
'''




'''
#Medicion 6
#58 minutos de integracion, 3635 datos --> 0.96 segundos por dato
#Por el usuario
BW=4e6 # Ancho de banda de RF
ganancia=38
center_freq=1010e6
B= 1.483 #Baseline [m]
freq=11e9 # Frecuencia del cielo
dec_deg=-12.27 #deg
samp_rate=8e6
fft_size=1024
fft_rate=30
start=14*3600+(05*60) # hora de inicio de la medicion, en segundos. Hasta las 15:03
filename='20160224_data.txt'
'''





'''
#Medicion 7
# desde las 15:04 hasta las 15:52
#integra 48 minutos
#Por el usuario

BW=1e6 # Ancho de banda de RF
ganancia=38
center_freq=3.025e9
B= 1.483 #Baseline [m]
freq=11e9 # Frecuencia del cielo
dec_deg=-12.27 #deg
samp_rate=1e6
fft_size=1024
fft_rate=30
start=15*3600+(04*60) # hora de inicio de la medicion, en segundos
filename='20160224_data2.txt'
'''





'''
#Medicion 8
# desde las 09:40 hasta las 14:50

#Por el usuario

BW=8e6 # Ancho de banda de RF
ganancia=38
center_freq=1010e6
B= 1.483 #Baseline [m]
freq=11e9 # Frecuencia del cielo
dec_deg=-12.27 #deg
samp_rate=1e6
fft_size=1024
fft_rate=30
start=9*3600+(40*60) # hora de inicio de la medicion, en segundos
filename='20160226_data.txt'
'''



#Calculados
c= 3.0e8# Velocidad de la luz [m/s]
wv= c/freq #Longitud de onda [m] 
dec= dec_deg*pi/180 #rad


#Leer datos
floats = []
with open(filename, "rb") as f:
    word = f.read(4)
    while word != "":
        floats.append(struct.unpack('f', word)[0])
        word = f.read(4)


#Get time
rate=1.0/0.96#(samp_rate/fft_rate/30/fft_size)#cantidad de datos por segundos
print "Cantidad de datos por segundo: " + str(rate)
time_step=1.0/(rate) #segundos
print "Tiempo en que tarda en cada dato (seg): " + str(time_step)
stop=time_step*len(floats)+start
print start
print stop
#print "time step "+ str(time_step)
time1=arange(start,stop,time_step)#start, stop, step
#print str(len(time1))
print "cantidad de tiempos: "+ str(len(time1))
print "cantidad de datos: "+ str(len(floats))
print "tiempo de adquisicion: "+ str(((time1[len(floats)-1])-(time1[0]))/3600) + " horas"

wv= c/freq #Longitud de onda [m] 
Bl_= B/wv #Bsublambda = B/ lambda
lB_=1/Bl_ #distancia entre peaks

#SD= diametro del sol

# Expansion de Taylor de la funcion sinc
# SD*(1-(((pi*Bl*SD)^2)/6))

#Suavizar con filtro pasabandas

fou=np.fft.fft(floats)


#suavizar datos con filtro pasabajos
a=20
f1 = np.linspace(start-start-((stop-start)/2), stop-start-((stop-start)/2), len(floats))#start, stop, cantidad de datos
filtro=a*mysinc(f1,a)

#plt.plot(f1,filtro)
floats_conv=np.convolve(filtro, floats)#filtrado con pasabanda centrado en cero, para frecuencias desde -a hasta a
#plt.plot(floats_conv)
plt.plot(f1,fou)


filt1=myrect(f1,a)
plt.plot(f1,filt1)

done=mymult(fou,filt1)
done2=myfilt(f1,a,fou)
plt.plot(f1,done2)


fouinv=np.fft.ifft(done2)
plt.plot(f1,fouinv)


#Encontrar maximo y minimo de potencia

plt.figure()
plt.plot(time1[20:len(floats)-1]/3600, floats[20:len(floats)-1])
plt.ylabel('PSD [mW]')
plt.xlabel('time [h]')
plt.title('PSD')


b=bool(0)
print b
while (not b):
	print "Click en la maxima potencia"
	pts_max = plt.ginput(1) 
	print str(pts_max)
	bol=input("Correcto?: True / False")
	b=bool(bol)	
	time.sleep(1)




print "Click en la minima potencia"
pts_min = ginput(1) 

x_max=map(lambda x: x[0],pts_max) # map applies the function passed as 
y_max=map(lambda x: x[1],pts_max) # first parameter to each element of pts

x_min=map(lambda x: x[0],pts_min) # map applies the function passed as 
y_min=map(lambda x: x[1],pts_min) # first parameter to each element of pts


#Lo mismo para obtener el periodo

print "Click en un valle"
pts_v1 = ginput(1) 
print "Click en el valle consecutivo"
pts_v2 = ginput(1) 

x_v1=map(lambda x: x[0],pts_v1) # map applies the function passed as 
y_v1=map(lambda x: x[1],pts_v1) # first parameter to each element of pts

x_v2=map(lambda x: x[0],pts_v2) # map applies the function passed as 
y_v2=map(lambda x: x[1],pts_v2) # first parameter to each element of pts

plt.draw()
#plt.show()

Pmax=y_max[0]
Pmin=y_min[0]
d1= x_v1[0]
d2=x_v2[0]
dis_peaks=(abs(d1-d2))*3600

#Pmax= 0.850799
#Pmin=0.783757
#dis_peaks=(12.6533-12.6155)*3600 #segundos




print "Pmin: " + str(Pmin)	
print "Pmax: " + str(Pmax)	
print "Tiempo entre peaks: " + str(dis_peaks)+ " segundos"	
#print str(time_step)
sun_v=2*pi/(24.0*3600.0)* cos(dec)  #velocidad angular del sol [rad/seg]. Da 2pi rad en 24 hrs es la maxima
print "velocidad sol: "+str(sun_v)+ " [rad/seg]"

rads=array(time1)*sun_v# transformacion de tiempo a grados, segun la velocidad del sol
#print str(max(rads))



dis_ang_peaks=dis_peaks*sun_v #distancia entre peaks en radianes
#Luego distancia entre peaks= longitud de onda/ Baseline
lB=dis_ang_peaks
Bl=1/lB

print "Baseline calculada: " +str(wv*Bl)
print "Baseline medida: " + str(B)



Visibilidad=(Pmax-Pmin)/(Pmax+Pmin)

print "visibilidad: " + str(Visibilidad)

#H= (pi*pi* Bl*Bl)/6
#H_=(pi*pi* Bl_*Bl_)/6# utilizando baseline medido
#from scipy.optimize import fsolve

#Resolviendo la ecuacion:
#def poly(t):
#	return (t-(H*t*t*t)-Visibilidad)

#def poly_(t):
#	return (t-(H_*t*t*t)-Visibilidad)

#SD=fsolve(poly,0.1)
#SD_=fsolve(poly_,0.1)
SD= (math.sqrt(6)/pi)*(lB)*(math.sqrt(1-Visibilidad))
SD_= (math.sqrt(6)/pi)*(lB_)*(math.sqrt(1-Visibilidad))
print "Diametro del sol con baseline calculada: " + str(SD)+ " [rad]"
print "Diametro del sol con baseline medida: " + str(SD_)+ " [rad]"

# Transformar a arcmin
sd_deg=SD*360/(2*pi)#deg
sd_deg_=SD_*360/(2*pi)#deg
print "Diametro del sol (baseline calculada): " + str(sd_deg)+ " [deg]"
print "Diametro del sol (baseline medida): " + str(sd_deg_)+ " [deg]"
sd_deg_norm=sd_deg-((int(sd_deg)/int(360))*360)#quitar revoluciones enteras extra
sd_armin=sd_deg_norm*60 # arcmin
print "Diametro del sol (con baseline calculada): " + str(sd_armin)+ " [arcmin]"



plt.show()


'''
Primeros resultados


Pmin: 1.20442152023
Pmax: 1.73858630657
Tiempo entre peaks: 796
velocidad sol: 7.27220521664e-05 [rad/seg]
0.928951494374
visibilidad: 0.181503012487
/usr/lib/python2.7/dist-packages/scipy/optimize/minpack.py:236: RuntimeWarning: The iteration is not making good progress, as measured by the 
  improvement from the last ten iterations.
  warnings.warn(msg, RuntimeWarning)
Diametro del sol: [ 0.0260442] [rad]
Diametro del sol: [ 1.49222246] [deg]
Diametro del sol: [ 1.49222246] [deg]


Resultados actuales:

ldauvin@nb-ldauvin:~/Desktop$ python offline_proc.py 
cantidad de datos: 12775
tiempo de adquisicion: 3.99968688845 horas
Pmin: 1.20442152023
Pmax: 1.73858630657
Tiempo entre peaks: 897.252446184
velocidad sol: 7.27220521664e-05 [rad/seg]
visibilidad: 0.181503012487
Diametro del sol: [-0.08877131] [rad]
Diametro del sol: [-5.08622123] [deg]
Diametro del sol: [ 354.91377877] [deg]





:(

'''

