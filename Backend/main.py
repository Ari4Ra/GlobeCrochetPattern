from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pyproj import Transformer
import xarray as xr
import glob
#from ipyleaflet import CircleMarker
import math
from fastapi.middleware.cors import CORSMiddleware

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


class PatternGenerator:
    def __init__(self, loader, stitch_coordinates):
        self.loader = loader
        self.st = stitch_coordinates

    def generate(self):
        info = self.st.doublestitches()
        for n in range(len(self.st.doublestitches())):
            for i in range(len(self.st.doublestitches()[n])):
                if self.st.doublestitches()[n][i] <= 0:
                    info[n][i] = [info[n][i], colorword(self.loader.lookup(*self.st.coordinates()[n][i]))]
                else:
                    info[n][i] = [info[n][i], colorword(self.loader.lookup(*self.st.coordinates()[n][i])),
                                  colorword(self.loader.lookup(*self.st.coordinates()[n][i + 1]))]
        pat = []
        for n in range(len(self.st.doublestitches())):
            w = 1
            pat.append([])
            for i in range(len(self.st.doublestitches()[n]) - 1):
                if info[n][i] == info[n][i + 1]:
                    w = w + 1
                else:
                    pat[n].append([w, " mal ", *info[n][i]])
                    w = 1
                    if i == len(self.st.doublestitches()[n]) - 2:
                        pat[n].append([1, " mal ", *info[n][i + 1]])
            if w == len(self.st.doublestitches()[n]):
                pat[n].append([w, " mal ", *info[n][0]])
        return pat


def colorword(n):
    if n in range(1, 6):
        return 'green'
    elif n in range(6, 11):
        return 'olive'
    elif n in range(11, 16):
        return 'green'
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
    #path: str


@app.post("/generate")
def generate(req: GenerateRequest):
    try:
        stitch_coordinates = StitchCoordinates(req.stitchlength, req.stitchheight, req.stitchsetback, req.diametercm)
        #loader=Loader("C:\\Users\\arian\\OneDrive\\Dokumente\\GitHub\\GlobeCrochetPattern\\Data\\*.tif")
        pattern_generator=PatternGenerator(GLOBAL_LOADER, stitch_coordinates)
        #coords = st.coordinates()
        #flat = [p for row in coords for p in row]
        #return {"markers": flat}
        return pattern_generator.generate()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))