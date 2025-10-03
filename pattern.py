import math

import xarray as xr
import gzip
import shutil

stitchlength=3
stitchheight=3
stitchsetback=1
diameter=30
diametermm=diameter*10

#with gzip.open('ETOPO1_Ice_g_gmt4.grd.gz', 'rb') as f_in:
#

ds = xr.open_dataset('ETOPO1_Ice_g_gmt4.grd')        

initialstitches=round(math.pi*diametermm*math.sin(2*stitchheight/diametermm)/stitchlength)
numberofrows=math.ceil(math.pi*diametermm/(2*stitchheight))
#numberofrows=100 #test number
numberofstitches=[0]*numberofrows
#numberofstitches[0]=initialstitches
numberofdoublestitches=[0]*numberofrows
#numberofdoublestitches[0]=initialstitches
isdoublestitch=[None]*numberofrows

coordinates=[0]*numberofrows
coordinates[0]=[0]*initialstitches

for n in range(numberofrows):
    if n< math.floor((numberofrows-1)/2)+1: #Südhalbkugel
        if n==0:
            numberofstitches[n]=initialstitches
            numberofdoublestitches[n]=initialstitches
            isdoublestitch[n]=[False]*initialstitches
        if round(math.pi*diametermm*math.sin(2*(n+1)*stitchheight/diametermm)/stitchlength)>numberofstitches[n-1]+numberofstitches[0]: #verhindern, dass man Maschen verdreifachen muss (in der ersten Reihe), bzw. mehr als die Anfangsmaschenzahl zugenommen wird
            numberofstitches[n]=numberofstitches[n-1]+initialstitches
        else:
            numberofstitches[n]=round(math.pi*diametermm*math.sin(2*(n+1)*stitchheight/diametermm)/stitchlength)
        numberofdoublestitches[n]=numberofstitches[n]-numberofstitches[n-1]
        isdoublestitch[n]=[False]*numberofstitches[n]
        if numberofdoublestitches[n]>0:
            distancebetweendoublestitches=math.floor(numberofstitches[n]/numberofdoublestitches[n])#including one endpoint
            error=numberofstitches[n]-distancebetweendoublestitches*numberofdoublestitches[n]
            print("error=",error)
        for i in range(0,numberofdoublestitches[n]):
            if n%2==0:
                isdoublestitch[n][i*distancebetweendoublestitches]=True
            else:
                isdoublestitch[n][i*distancebetweendoublestitches+math.floor(distancebetweendoublestitches/2)]=True
    else: #Nordhalbkugel
         numberofstitches[n]=numberofstitches[numberofrows-n-1]
         numberofdoublestitches[n]=numberofstitches[n-1]-numberofstitches[n]
         isdoublestitch[n]=isdoublestitch[numberofrows-n-1]
    coordinates[n]=[0]*numberofstitches[n]    



for n in range(0,numberofrows):
    for k in range(0,numberofstitches[n]):
        if isdoublestitch[n][k]:
            print("X",end="")
        else:
            print("o",end="")
    print("\n")

    print(ds)
    
#print(numberofstitches)
#print(numberofdoublestitches)
#print(isdoublestitch)
#print(coordinates)