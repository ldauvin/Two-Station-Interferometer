# Leer datos de FFTs en el tiempo
filename='canales_fft'



import struct
import matplotlib.pyplot as plt
import numpy as np
import math
import time
from numpy import *
from pylab import plot, ginput, show, axis

fft_size=1024

#Leer datos
floats = []
with open(filename, "rb") as f:
    word = f.read(4)
    while word != "":
        floats.append(struct.unpack('f', word)[0])
        word = f.read(4)


print len(floats)

# Llevara canales
can_fft=len(floats)/fft_size #numero de ffts que se obtuvieron
print can_fft
print can_fft*fft_size
chan=np.zeros((fft_size,can_fft ))#ffts dispuestas en columnas de 1024 filas (fft_size)
chan2=np.zeros((can_fft,fft_size ))#ffts dispuestas en columnas de 1024 filas (fft_size), para ver ffts
cont=0
for i in range (0,can_fft):
	#print i
	for j in range (0,fft_size):
		chan[j][i]=floats[cont]
		chan2[i][j]=floats[cont]
		cont=cont+1
		#print j
print cont


plt.plot(chan[:][0])#Cada canal en el tiempo
#plt.plot(chan2[:][0])#cada FFT
#plt.plot(floats)
plt.show()
