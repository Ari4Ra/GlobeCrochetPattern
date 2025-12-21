from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pyproj import Transformer
import xarray as xr
import glob
#from ipyleaflet import CircleMarker
import math
from fastapi.middleware.cors import CORSMiddleware
import rasterio
from rasterio.windows import from_bounds, Window, WindowError
from collections import Counter
import numba
import numpy as np
from rasterio.transform import rowcol
#import rioxarray

class Loader:
    def __init__(self, path_pattern: str):
        """Lädt nur die Metadaten für schnelle Initialisierung."""
        self.files = glob.glob(path_pattern)
        self.dss = []
        self.bounds = []

        for fp in self.files:
            ds = xr.open_dataset(fp, engine="rasterio")
            self.dss.append(ds)
            # Bounds als (minx, miny, maxx, maxy)
            self.bounds.append((
                round(float(ds.x.min())),
                round(float(ds.y.min())),
                round(float(ds.x.max())),
                round(float(ds.y.max()))
            ))

    def lookup(self, lat, lon) -> int | None:
        for i, bound in enumerate(self.bounds):
            if bound[0] <= lon <= bound[2] and bound[1] <= lat <= bound[3]:
                ds = self.dss[i]

                # CRS-sicher
                if ds.rio.crs is not None and ds.rio.crs.to_epsg() != 4326:
                    transformer = Transformer.from_crs("EPSG:4326", ds.rio.crs, always_xy=True)
                    xx, yy = transformer.transform(lon, lat)
                else:
                    xx, yy = lon, lat

                try:
                    val = ds.sel(x=xx, y=yy, method="nearest")["band_data"].values[0]
                    return int(val)
                except IndexError:
                    return None
        return None

    def lookup_majority_window(self, lat, lon, dlat, dlon, max_samples=10):
        min_lat, max_lat = lat - dlat, lat + dlat
        min_lon, max_lon = lon - dlon, lon + dlon
        for i, bound in enumerate(self.bounds):
            if bound[0] <= lon <= bound[2] and bound[1] <= lat <= bound[3]:
                ds = self.dss[i]

                if ds.rio.crs is not None and ds.rio.crs.to_epsg() != 4326:
                    transformer = Transformer.from_crs("EPSG:4326", ds.rio.crs, always_xy=True)
                    xmin, ymin = transformer.transform(min_lon, min_lat)
                    xmax, ymax = transformer.transform(max_lon, max_lat)
                else:
                    xmin, ymin = max(min_lon,bound[0]), max(min_lat, bound[1])
                    xmax, ymax = min(max_lon, bound[2]), min(max_lat, bound[3])

                row_min, col_min = rowcol(ds.rio.transform(), xmin, ymax)
                row_max, col_max = rowcol(ds.rio.transform(), xmax, ymin)

                row_min = max(0, min(ds.sizes["y"] - 1, row_min))
                row_max = max(0, min(ds.sizes["y"] - 1, row_max))
                col_min = max(0, min(ds.sizes["x"] - 1, col_min))
                col_max = max(0, min(ds.sizes["x"] - 1, col_max))

                patch = ds["band_data"].isel(
                    y=slice(row_min, row_max + 1),
                    x=slice(col_min, col_max + 1)
                ).values

                # Downsampling
                step_y = max(1, patch.shape[0] // max_samples)
                step_x = max(1, patch.shape[1] // max_samples)
                patch_ds = patch[::step_y, ::step_x]

                if patch_ds.size == 0:
                    return None

                vals, counts = np.unique(patch_ds, return_counts=True)
                return int(vals[np.argmax(counts)])
        return None


    def lookup_majority_batch_flat(self, coords, dlat, dlon, max_samples=50):
        results = [None] * len(coords)
        for idx, (lat, lon) in enumerate(coords):
            results[idx] = self.lookup_majority_window(lat, lon, dlat, dlon, max_samples)
        return results

    def lookup_majority_batch_nested(self, coords_nested, dlat, dlon, max_samples=50):
        results_nested = []
        for sublist in coords_nested:
            results_nested.append(self.lookup_majority_batch_flat(sublist, dlat, dlon, max_samples))
        return results_nested


class StitchCoordinates:
    def __init__(self, stitchlength, stitchheight, stitchsetback, diametercm):
        self.stitchlength = stitchlength
        self.stitchheight = stitchheight
        self.stitchsetback = stitchsetback
        self.diametermm = diametercm * 10
        self.r = self.diametermm / 2
        self.initialstitches = round(math.pi * self.diametermm * math.sin(self.stitchheight / self.r) / self.stitchlength)
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
                ((self.numberofstitches[n]-1-i)*self.deg[n]/self.numberofstitches[n]+self.sumdegsetback[n])%360-180]) # Latitude, Longitude
        return co

    def doublestitches(self):
        diff=[self.initialstitches]
        dist=[0]
        rest=[0]
        abzu=[1] #1=Zunahme, -1=Abnahme, 0= weder noch
        ds=[[0]*self.initialstitches]
        for n in range(1,self.numberofrows):
            #print("n=",n)
            diff.append(abs(self.numberofstitches[n]-self.numberofstitches[n-1]))
            #print("diff=",diff)
            if (self.numberofstitches[n]-self.numberofstitches[n-1])>0:
                abzu.append(1)
            elif (self.numberofstitches[n]-self.numberofstitches[n-1])<0:
                abzu.append(-1)
            else:
                abzu.append(0)
            #print("abzu=",abzu)
            if abzu[n]!=0:
                dist.append(math.floor(self.numberofstitches[n-1]/diff[n]))
            else:
                dist.append(self.numberofstitches[n-1])
            #print("dist=",dist)
            rest.append(self.numberofstitches[n-1]-diff[n]*dist[n])
            #print("rest=",rest)
            h=[]
            for i in range(diff[n]): #es wird pro Durchlauf eine Masche abgenommen oder zugenommen
                #print("i=",i)
                #print("diff[n]=",diff[n])
                #print("dist[n]=",dist[n])
                if abzu[n]==1:
                    if i<rest[n]: #der Rest wird auf die ersten Zunahmen aufgeteilt
                        h.extend([0]*dist[n])
                        h.append(1)
                    else:
                        h.extend([0] * (dist[n]-1))
                        h.append(1)
                    # Insgesamt werden in der n-ten Reihe diff[n] Increases und rest[n]*dist[n]+ (diff[n]-rest[n])*dist[n] sc gehäkelt. Insgesamt:
                elif abzu[n]==-1:
                    if i < rest[n]:
                        h.extend([0] * (dist[n]-1))
                        h.append(-1)
                    else:
                        h.extend([0] * (dist[n] - 2))
                        h.append(-1)
            if abzu[n]==0: #falls die Maschenanzahl gleich bleibt
                h.extend([0] * (dist[n]))
            #print("n=",n)
            #print(h)
            shift=math.floor(2*self.numberofstitches[n]/5)
            h=h[-shift:] + h[:-shift]
            #print(h)
            ds.append(h)
        return ds


class PatternGenerator:
    def __init__(self, loader, stitch_coordinates):
        self.loader = loader
        self.st = stitch_coordinates
        dlat = min(3, (90 / math.pi) * stitch_coordinates.stitchheight / stitch_coordinates.r)
        dlon = min(3, (90 / math.pi) * stitch_coordinates.stitchlength / stitch_coordinates.r)
        farb = self.loader.lookup_majority_batch_nested(self.st.coordinates(), dlon, dlat,10)
        self.info = [[] for _ in range(self.st.numberofrows)]
        for n in range(len(self.st.doublestitches())):
            x=[]
            h=0
            for i in range(len(self.st.doublestitches()[n])):
                if self.st.doublestitches()[n][i] <= 0:
                    #self.info[n][i] = [self.info[n][i], colorword(farb[n][i])]
                    self.info[n].append([self.st.doublestitches()[n][i], colorword(farb[n][h])])
                    h+=1
                elif self.st.doublestitches()[n][i]==1:
                    self.info[n].append([self.st.doublestitches()[n][i], colorword(farb[n][h]),
                                  colorword(farb[n][h+1])])
                    h+=2
                #else:
                 #   x.append(i)
                  #  h=0
            #print(n, "jiofsd", x)
            #for j in sorted(x, reverse=True):
                #del self.info[n][j]




    def generate(self):
        pat = []
        for n in range(len(self.info)):
            w = 1
            pat.append([])
            for i in range(len(self.info[n]) - 1):
                if self.info[n][i] == self.info[n][i + 1]:
                    w = w + 1
                    if i == len(self.info[n]) - 2:
                        pat[n].append([w, " mal ", *self.info[n][i]])
                else:
                    pat[n].append([w, " mal ", *self.info[n][i]])
                    w = 1
                    if i == len(self.info[n]) - 2:
                        pat[n].append([1, " mal ", *self.info[n][i + 1]])
        return pat

    def statistik(self):
        am={"green": 0, "olive":0, "dark gray": 0, "yellow":0, "light gray":0, "white":0, "blue":0, "sand":0, "total":0}
        for n in range(len(self.info)):
            for i in range(len(self.info[n])):
                match self.info[n][i][1]:
                    case "green":
                        am["green"] += 1
                    case "olive":
                        am["olive"] += 1
                    case "dark gray":
                        am["dark gray"] += 1
                    case "yellow":
                        am["yellow"] += 1
                    case "light gray":
                        am["light gray"] += 1
                    case "white":
                        am["white"] += 1
                    case "blue":
                        am["blue"] += 1
                    case "sand":
                        am["sand"] +=1
                if self.info[n][i][0]==1:
                    match self.info[n][i][2]:
                        case "green":
                            am["green"] += 1
                        case "olive":
                            am["olive"] += 1
                        case "dark gray":
                            am["dark gray"] += 1
                        case "yellow":
                            am["yellow"] += 1
                        case "light gray":
                            am["light gray"] += 1
                        case "white":
                            am["white"] += 1
                        case "blue":
                            am["blue"] += 1
                        case "sand":
                            am["sand"] +=1
        am["total"]=(am["green"]+am["olive"]+am["dark gray"]+am["yellow"]+am["light gray"]+am["white"]+am["blue"]+am["sand"])
        return am


def colorword(n):
    if n in range(1, 7) or n==9 or n in range(11,16):
        return 'green'
    elif n==7 or n==10:
        return 'sand'
    elif n==8:
        return 'olive'
    elif n == 16:
        return 'dark gray'
    elif n == 17:
        return 'yellow'
    elif n == 18:
        return 'light gray'
    elif n == 19:
        return 'white'
    elif n == 20:
        return 'blue'
    else:
        return 'error'



# --- FastAPI Setup ---
app = FastAPI()

print("Lade TIFF-Daten... (einmalig)")
GLOBAL_LOADER = Loader("C:\\Users\\arian\\OneDrive\\Dokumente\\GitHub\\GlobeCrochetPattern\\Data\\*.tif")
print("Loader geladen!")

# CORS Setup
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    stitchlength: float
    stitchheight: float
    stitchsetback: float
    diametercm: float
    lengthoftestyarn: float
    amountofteststitches: float
    #path: str


@app.post("/generate")
def generate(req: GenerateRequest):
    try:
        stitch_coordinates = StitchCoordinates(req.stitchlength, req.stitchheight, req.stitchsetback, req.diametercm)
        #loader=Loader("C:\\Users\\arian\\OneDrive\\Dokumente\\GitHub\\GlobeCrochetPattern\\Data\\*.tif")
        pattern_generator=PatternGenerator(GLOBAL_LOADER, stitch_coordinates)
        ratio=req.lengthoftestyarn/req.amountofteststitches
        original= pattern_generator.statistik()
        new_stats = {
            color: {"count": count, "length": ratio*count}
            for color, count in original.items()
        }

        #coords = st.coordinates()
        #flat = [p for row in coords for p in row]
        #return {"markers": flat}
        return {
            "pattern": pattern_generator.generate(),
            "statistics": new_stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))