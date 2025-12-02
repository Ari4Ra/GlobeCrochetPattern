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


@numba.njit
def majority_numba(arr):
    """
    Berechnet den Mehrheitswert eines 1D Integer-Arrays (Masking vorher erledigen).
    """
    arr = np.asarray(arr, dtype=np.int32)  # Numba-freundlich

    if arr.size == 0:
        return -1  # fallback

    min_val = arr[0]
    max_val = arr[0]

    # Manuelles min/max für Numba
    for i in range(1, arr.size):
        if arr[i] < min_val:
            min_val = arr[i]
        elif arr[i] > max_val:
            max_val = arr[i]

    counts = np.zeros(max_val - min_val + 1, dtype=np.int32)

    for i in range(arr.size):
        counts[arr[i] - min_val] += 1

    idx = 0
    max_count = counts[0]
    for i in range(1, counts.size):
        if counts[i] > max_count:
            max_count = counts[i]
            idx = i

    return idx + min_val

# ----------------------
# Loader Klasse
# ----------------------
class Loader:
    def __init__(self, path_pattern: str):
        self.files = glob.glob(path_pattern)
        self.dss = []
        self.bounds = []
        self.transformers = []

        for fp in self.files:
            ds = rasterio.open(fp)
            arr = ds.read(1, masked=True)  # masked Array
            self.dss.append({
                "array": arr,
                "transform": ds.transform,
                "crs": ds.crs,
                "nodata": ds.nodata,
                "width": ds.width,
                "height": ds.height,
                "path": fp
            })
            self.bounds.append(ds.bounds)
            self.transformers.append(Transformer.from_crs("EPSG:4326", ds.crs, always_xy=True))

    # ----------------------
    # Flache Batch-Methode (für interne Nutzung)
    # ----------------------
    def lookup_majority_batch_flat(self, coords, dlat, dlon):
        results = [None] * len(coords)

        for ds, bounds, transformer in zip(self.dss, self.bounds, self.transformers):
            inside_indices = [i for i, (lat, lon) in enumerate(coords)
                              if bounds.left <= lon <= bounds.right and bounds.bottom <= lat <= bounds.top]
            if not inside_indices:
                continue

            lats = np.array([coords[i][0] for i in inside_indices])
            lons = np.array([coords[i][1] for i in inside_indices])

            min_lat, max_lat = lats.min() - dlat, lats.max() + dlat
            min_lon, max_lon = lons.min() - dlon, lons.max() + dlon

            xmin, ymin = transformer.transform(min_lon, min_lat)
            xmax, ymax = transformer.transform(max_lon, max_lat)

            row_min, col_min = rasterio.transform.rowcol(ds["transform"], xmin, ymax)
            row_max, col_max = rasterio.transform.rowcol(ds["transform"], xmax, ymin)

            row_min = max(0, min(ds["height"] - 1, row_min))
            row_max = max(0, min(ds["height"] - 1, row_max))
            col_min = max(0, min(ds["width"] - 1, col_min))
            col_max = max(0, min(ds["width"] - 1, col_max))

            sub = ds["array"][row_min:row_max + 1, col_min:col_max + 1]

            for idx in inside_indices:
                lat, lon = coords[idx]
                r, c = rasterio.transform.rowcol(ds["transform"], lon, lat)
                r_sub, c_sub = r - row_min, c - col_min

                r0 = max(0, r_sub - int(dlat * 111000 / ds["transform"].a))
                r1 = min(sub.shape[0] - 1, r_sub + int(dlat * 111000 / ds["transform"].a))
                c0 = max(0, c_sub - int(dlon * 111000 / ds["transform"].a))
                c1 = min(sub.shape[1] - 1, c_sub + int(dlon * 111000 / ds["transform"].a))

                patch = sub[r0:r1 + 1, c0:c1 + 1]
                if patch.mask.all():
                    results[idx] = None
                else:
                    results[idx] = majority_numba(patch.compressed())

        return results

    # ----------------------
    # Verschachtelte Batch-Methode
    # ----------------------
    def lookup_majority_batch_nested(self, coords_nested, dlat, dlon):
        """
        coords_nested: Liste von Listen von Koordinaten [[(lat, lon), ...], ...]
        Gibt die gleiche verschachtelte Struktur zurück mit Mehrheitswerten.
        """
        results_nested = []
        for sublist in coords_nested:
            sub_results = self.lookup_majority_batch_flat(sublist, dlat, dlon)
            results_nested.append(sub_results)
        return results_nested

class PatternGenerator:
    def __init__(self, loader, stitch_coordinates):
        self.loader = loader
        self.st = stitch_coordinates
        dlat=abs(self.st.coordinates()[0][0][0]-self.st.coordinates()[1][0][0])
        dlon=abs(self.st.coordinates()[0][0][1]-self.st.coordinates()[0][1][1])
        farb = self.loader.lookup_majority_batch_nested(self.st.coordinates(), dlat, dlon)
        self.info = self.st.doublestitches()
        for n in range(len(self.st.doublestitches())):
            for i in range(len(self.st.doublestitches()[n])):
                if self.st.doublestitches()[n][i] <= 0:
                    self.info[n][i] = [self.info[n][i], colorword(farb[n][i])]
                else:
                    self.info[n][i] = [self.info[n][i], colorword(farb[n][i]),
                                  colorword(farb[n][i+1])]


    def generate(self):
        #info = self.st.doublestitches()
        #for n in range(len(self.st.doublestitches())):
         #   for i in range(len(self.st.doublestitches()[n])):
          #      if self.st.doublestitches()[n][i] <= 0:
             #       info[n][i] = [info[n][i], colorword(self.loader.lookup(*self.st.coordinates()[n][i]))]
           ##     else:
              #      info[n][i] = [info[n][i], colorword(self.loader.lookup(*self.st.coordinates()[n][i])),
               #                   colorword(self.loader.lookup(*self.st.coordinates()[n][i + 1]))]
        pat = []
        for n in range(len(self.st.doublestitches())):
            w = 1
            pat.append([])
            for i in range(len(self.st.doublestitches()[n]) - 1):
                if self.info[n][i] == self.info[n][i + 1]:
                    w = w + 1
                else:
                    pat[n].append([w, " mal ", *self.info[n][i]])
                    w = 1
                    if i == len(self.st.doublestitches()[n]) - 2:
                        pat[n].append([1, " mal ", *self.info[n][i + 1]])
            if w == len(self.st.doublestitches()[n]):
                pat[n].append([w, " mal ", *self.info[n][0]])
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