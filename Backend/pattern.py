import math
from pyproj import Transformer

import xarray as xr
import glob
from ipyleaflet import CircleMarker
from rasterio.windows import from_bounds, Window, WindowError
import numpy as np
from collections import Counter
import rasterio
def color(n):
    if n in range(1,6):
        return '#11451e'
    elif n in range(6,11):
        return '#b9c23c'
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


def colorr(n):
    if n in range(1,6): #forest
        return '#476e3d'
    elif n in range(6,7): #tree open
        return '#476e3d'#'#615c49'#grünschwarz  #'4c4734'
    elif n==7: #shrub
        return '#c99d75'#'#dbf20c'#neongrün#615c49'#grünschwarz'#cc8551' #caramel
    elif n==8: #herbaceous
        return '#c99d75'#f6aa48'#'#db291d' #red
    elif n==9: #herbaceous with sparse tree/shrub
        return '#476e3d'#'#51edeb' #türkis
    elif n==10: #sparse vegetation
        return '#c99d75'#5c3305' #braun
    elif n in range(11,16): #ackerland, sumpf, mangroven
        return '#476e3d' #grün
    elif n==16: #steinwüste
        return '#6e6d75'#'#bcbbc0' #grau
    elif n==17: #sandwüste
        return '#f6aa48'#c99d75'#fcd267' #gelb
    elif n==18: #urban
        return '#a7a9ab'
    elif n==19: #snow/ice
        return '#ffffff' #weiß
    elif n==20: #water
        return '#4778ba' #blau
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
        self.numberofstitches=[]
        self.calculatenumberofstitches()
        self.deg=[]
        self.rad=[]
        self.sumdegsetback=[]
        self.calculatesetback()

    def calculatenumberofstitches(self):
        nos=[self.initialstitches]
        for n in range(1, self.numberofrows):
            if n < math.floor((self.numberofrows - 1) / 2) + 1:  # southern hemisphere
                if round((math.pi * self.diametermm * math.sin(2 * (n + 1) * self.stitchheight / self.diametermm)+self.stitchsetback) / self.stitchlength) > nos[n - 1] + nos[0]:  # no triple increases in the second row
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

    def doublestitches(self):
        diff=[self.initialstitches]
        dist=[0]
        rest=[0]
        abzu=[1] #1=Zunahme, -1=Abnahme, 0= weder noch
        ds=[[0]*self.initialstitches]
        for n in range(1,self.numberofrows):
            diff.append(abs(self.numberofstitches[n]-self.numberofstitches[n-1]))
            if (self.numberofstitches[n]-self.numberofstitches[n-1])>0:
                abzu.append(1)
            elif (self.numberofstitches[n]-self.numberofstitches[n-1])<0:
                abzu.append(-1)
            else:
                abzu.append(0)
            if abzu[n]!=0:
                dist.append(math.floor(self.numberofstitches[n-1]/diff[n]))
            else:
                dist.append(self.numberofstitches[n-1])
            rest.append(self.numberofstitches[n-1]-diff[n]*dist[n])
            h=[]
            #print("aaaaaaaaaaaaaaaaa")
            #print(diff[n])
            #print(dist[n])
            #print(rest[n])
            #print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzz")
            for i in range(diff[n]):
                if abzu[n]==1:
                    if i<rest[n]:
                        h.extend([0]*dist[n])
                        h.append(1)
                    else:
                        h.extend([0] * (dist[n]-1))
                        h.append(1)
                elif abzu[n]==-1:
                    if i < rest[n]:
                        h.extend([0] * (dist[n]-1))
                        h.append(-1)
                    else:
                        h.extend([0] * (dist[n] - 2))
                        h.append(-1)
                else:
                    h.extend([0] * (dist[n]))
            #print(h)
            shift=math.floor(2*self.numberofstitches[n]/5)
            h=h[-shift:] + h[:-shift]
            ds.append(h)
        return ds

import glob
import math
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from pyproj import Transformer, Geod


class Loader:
    def __init__(self, path_pattern: str):
        """
        Liest nur Metadaten. Kein RAM-heavy Laden.
        """
        self.files = glob.glob(path_pattern)
        self.dss = []
        self.bounds = []
        self.transformers = []

        for fp in self.files:
            ds = rasterio.open(fp)
            self.dss.append(ds)

            # bounds = (left, bottom, right, top)
            self.bounds.append(ds.bounds)

            # Transformer vorbereiten
            self.transformers.append(
                Transformer.from_crs("EPSG:4326", ds.crs, always_xy=True)
            )

    # -------------------------------------------------------------

    def lookup(self, lat, lon):
        """
        Einzelnes Pixel abfragen.
        """
        for ds, bounds, trans in zip(self.dss, self.bounds, self.transformers):
            if bounds.left <= lon <= bounds.right and bounds.bottom <= lat <= bounds.top:
                x, y = trans.transform(lon, lat)
                row, col = ds.index(x, y)
                return int(ds.read(1, window=((row, row + 1), (col, col + 1)))[0, 0])
        return None

    # -------------------------------------------------------------
    # >>> HIER DEINE METHODE, UNVERÄNDERT, aber korrekt integriert
    # -------------------------------------------------------------

    def lookup_majority_window(self, lat, lon, dlat, dlon):
        """
        Rechteck um (lat, lon) definieren und Mehrheitswert berechnen.

        dlat, dlon: halbe Höhe und Breite in Grad
                    => tatsächliches Fenster ist [lat - dlat, lat + dlat] × [lon - dlon, lon + dlon]
        """

        min_lat = lat - dlat
        max_lat = lat + dlat
        min_lon = lon - dlon
        max_lon = lon + dlon

        for i, bound in enumerate(self.bounds):

            # Liegt Zentrum in diesem Raster?
            if not (bound.left <= lon <= bound.right and bound.bottom <= lat <= bound.top):
                continue

            ds = self.dss[i]
            path = self.files[i]

            transformer = Transformer.from_crs("EPSG:4326", ds.crs, always_xy=True)

            xmin, ymin = transformer.transform(min_lon, min_lat)
            xmax, ymax = transformer.transform(max_lon, max_lat)

            window = from_bounds(xmin, ymin, xmax, ymax, transform=ds.transform)

            counter = Counter()

            # blockweises Lesen für RAM-Sicherheit
            with rasterio.open(path) as rio_ds:
                for ji, block_window in rio_ds.block_windows(1):

                    try:
                        intersect = block_window.intersection(window)
                    except WindowError:
                        continue

                    if intersect.width <= 0 or intersect.height <= 0:
                        continue

                    arr = rio_ds.read(1, window=intersect, masked=True)
                    counter.update(arr.compressed().tolist())

            if not counter:
                return None

            return counter.most_common(1)[0][0]

        # Falls kein Raster zuständig war
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

class PatternGenerator:
    def __init__(self, loader, stitch_coordinates):
        self.loader=loader
        self.st=stitch_coordinates
    def generate(self):
        info=self.st.doublestitches()
        for n in range(len(self.st.doublestitches())):
            for i in range(len(self.st.doublestitches()[n])):
                if self.st.doublestitches()[n][i]<=0:
                    info[n][i]=[info[n][i], colorword(self.loader.lookup(*self.st.coordinates()[n][i]))]
                else:
                    info[n][i] = [info[n][i], colorword(self.loader.lookup(*self.st.coordinates()[n][i])),colorword(self.loader.lookup(*self.st.coordinates()[n][i+1]))]
        pat=[]
        for n in range(len(self.st.doublestitches())):
            w=1
            pat.append([])
            for i in range(len(self.st.doublestitches()[n])-1):
                if info[n][i]==info[n][i+1]:
                    w=w+1
                else:
                    pat[n].append([w," mal ", info[n][i]])
                    w=1
                    if i==len(self.st.doublestitches()[n]) - 2:
                        pat[n].append([1, " mal ", info[n][i+1]])
            if w==len(self.st.doublestitches()[n]):
                pat[n].append([w," mal ", info[n][0]])
        return pat



def colorword(n):
    if n in range(1,6):
        return 'green'
    elif n in range(6,11):
        return 'olive'
    elif n in range(11,16):
        return 'green'
    elif n==16:
        return 'dark gray'
    elif n==17:
        return 'yellow'
    elif n==18:
        return 'light gray'
    elif n==19:
        return 'white'
    elif n==20:
        return 'blue'
    else:
        return 'error'
