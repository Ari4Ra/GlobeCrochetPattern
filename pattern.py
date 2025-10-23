import math
from pyproj import Transformer

import xarray as xr
import glob
from ipyleaflet import CircleMarker
import rioxarray
import sys

#xds = xr.open_dataset("C:\\Users\\arian\\OneDrive\\Dokumente\\GitHub\\GlobeCrochetPattern\\Data\\gm_lc_v3_1_1.tif", engine="rasterio")
#yds = xr.open_dataset("C:\\Users\\arian\\OneDrive\\Dokumente\\GitHub\\GlobeCrochetPattern\\Data\\gm_lc_v3_1_2.tif", engine="rasterio")
#zds = xr.open_dataset("C:\\Users\\arian\\OneDrive\\Dokumente\\GitHub\\GlobeCrochetPattern\\Data\\gm_lc_v3_2_1.tif", engine="rasterio")
#wds = xr.open_dataset("C:\\Users\\arian\\OneDrive\\Dokumente\\GitHub\\GlobeCrochetPattern\\Data\\gm_lc_v3_2_2.tif", engine="rasterio")



def coordinatesf(stitchlength, stitchheight, stitchsetback, diameter):
    diametermm=diameter*10
    r=diametermm/2

    initialstitches=round(math.pi*diametermm*math.sin(2*stitchheight/diametermm)/stitchlength)
    numberofrows=math.floor(math.pi*diametermm/(2*stitchheight))
#numberofrows=15 #test number
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
            elif round(math.pi*diametermm*math.sin(2*(n+1)*stitchheight/diametermm)/stitchlength)>numberofstitches[n-1]+numberofstitches[0]: #verhindern, dass man Maschen verdreifachen muss (in der ersten Reihe), bzw. mehr als die Anfangsmaschenzahl zugenommen wird
                numberofstitches[n]=numberofstitches[n-1]+initialstitches
            else:
                numberofstitches[n]=round(math.pi*diametermm*math.sin(2*(n+1)*stitchheight/diametermm)/stitchlength)
            numberofdoublestitches[n]=numberofstitches[n]-numberofstitches[n-1]
            isdoublestitch[n]=[False]*numberofstitches[n]
            if numberofdoublestitches[n]>0:
                distancebetweendoublestitches=math.floor(numberofstitches[n]/numberofdoublestitches[n])#including one endpoint
                #error=numberofstitches[n]-distancebetweendoublestitches*numberofdoublestitches[n]
                #print("error=",error)
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



#for n in range(numberofrows):
#    for k in range(0,numberofstitches[n]):
 #       if isdoublestitch[n][k]:
 #           print("X",end="")
  #      else:
   #         print("o",end="")
   # print("\n")

    for n in range(numberofrows):
        for i in range(numberofstitches[n]):
            coordinates[n][i]=[-90+(n+i/(numberofstitches[n]))*180*stitchheight/(math.pi*r), -180+i*360/numberofstitches[n]] #Latitude, Longitude
        #print(coordinates[n], "\n")
    return coordinates   


#def lookup(lat, lon):
 #   transformer = Transformer.from_crs("EPSG:4326", xds.rio.crs, always_xy=True)
  #  xx, yy = transformer.transform(lon, lat)
   # if lon <0 and lat>0: #Nordamerika
    #    return int(xds.sel(x=xx, y=yy, method="nearest")["band_data"].values[0])
    #elif lon>0 and lat >0: #Eurasien
     #   return int(yds.sel(x=xx, y=yy, method="nearest")["band_data"].values[0])
    #elif lon<0 and lat<0: # Südamerika
    #    return int(zds.sel(x=xx, y=yy, method="nearest")["band_data"].values[0])
    #elif lon>0 and lat<0: #Australien
    #    return int(wds.sel(x=xx, y=yy, method="nearest")["band_data"].values[0])
    #else: #zur Sicherheit, tritt eigentlich nicht ein
    #    return int(xds.sel(x=xx, y=yy, method="nearest")["band_data"].values[0])

def color(n):
    if n in range(1,6):
        return '#11451e'
    elif n in range(6,11):
        return '#424511'
    elif n in range(11,16):
        return '#11451e'
    elif n==16:
        return '#3d3d3b'
    elif n==17:
        return '#f2bd35'
    elif n==18:
        return '#a7a9ab'
    elif n==19:
        return '#ffffff'
    elif n==20:
        return '#085099'
    else:
        return '#000000'

class StitchCoordinates:
    def __init__(self, stitchlength, stitchheight, stitchsetback, diametercm):
        self.stitchlength = stitchlength
        self.stitchheight = stitchheight
        self.stitchsetback = stitchsetback
        self.diametermm = diametercm * 10
        self.r = self.diametermm / 2
        self.initialstitches = round(math.pi * self.diametermm * math.sin(2 * stitchheight / self.diametermm) / stitchlength)
        self.numberofrows = math.floor(math.pi * self.diametermm / (2 * stitchheight))
        self.numberofstitches=0
        self.calculatenumberofstitches()
        self.deg=[]
        self.rad=[]
        self.sumdegsetback=[]
        self.calculatesetback()

    def calculatenumberofstitches(self):
        nos=[self.initialstitches]
        for n in range(1, self.numberofrows):
            if n < math.floor((self.numberofrows - 1) / 2) + 1:  # southern hemisphere
                if round(math.pi * self.diametermm * math.sin(2 * (n + 1) * self.stitchheight / self.diametermm) / self.stitchlength) > \
                     nos[n - 1] + nos[0]:  # no triple increases in the first row
                    nos.append(nos[n - 1] + nos[0])
                else:
                    nos.append(round(
                        (math.pi * self.diametermm * math.sin(2 * (n + 1) * self.stitchheight / self.diametermm)+self.stitchsetback) / self.stitchlength))
            else: #northern hemisphere
                nos.append(nos[self.numberofrows-n-1])
        self.numberofstitches= nos

    def calculatesetback(self):
        sumdegsetback=[]
        deg=[]
        rad=[]
        for n in range(0, self.numberofrows):
            if n < math.floor((self.numberofrows - 1) / 2) + 1:
                rad.append(self.r*math.sin((n+1)*self.stitchheight/self.r))
            else:
                rad.append(self.r * math.sin(math.pi-(n + 1) * self.stitchheight / self.r))
            deg.append(360+self.stitchsetback/(math.pi*rad[n])*180)
            if n==0:
                sumdegsetback.append(deg[n])
            else:
                sumdegsetback.append(deg[n]+sumdegsetback[n-1])
        self.deg=deg
        self.rad=rad
        self.sumdegsetback=sumdegsetback

    def coordinates(self) -> list[list[tuple[float,float]]]:
        co=[]
        for n in range(self.numberofrows):
            co.append([])
            for i in range(self.numberofstitches[n]):
                co[n].append([-90 + (n + i / (self.numberofstitches[n])) * 180 * self.stitchheight / (math.pi * self.r),
                (i*self.deg[n]/self.numberofstitches[n]+self.sumdegsetback[n])%360-180]) # Latitude, Longitude
        return co



class Loader:
    def __init__(self, path: str):
        self.files: list[str] = glob.glob(path)
        self.dss: list[xr.Dataset] = [xr.open_dataset(ds, engine="rasterio") for ds in self.files]
        self.bounds: list[tuple[float,float,float,float]] = [(math.floor(min(ds.x)), math.floor(min(ds.y)),math.ceil( max(ds.x)), math.ceil(max(ds.y))) for ds in self.dss]

    def lookup(self, lat, lon) -> int | None:
        for i, bound in enumerate(self.bounds):
            if bound[0]<=lon<=bound[2] and bound[1]<=lat<=bound[3]:
                transformer = Transformer.from_crs("EPSG:4326", self.dss[i].rio.crs, always_xy=True)
                xx, yy = transformer.transform(lon, lat)
                return int(self.dss[i].sel(x=xx, y=yy, method="nearest")["band_data"].values[0])
        return None


def convert2markers(coordinatenliste, loader):
    markers=[]
    for row in coordinatenliste:
        for stitch in row:
            markers.append(
                CircleMarker(
                    location=stitch,
                    radius=2,
                    color="white",
                    fill_color=str(color(loader.lookup(*stitch))),
                    fill_opacity=0.9,
                    weight=0
                ))

    return markers
