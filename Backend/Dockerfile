FROM python:3.11-slim

# ---- system dependencies for rasterio / GDAL ----
RUN apt-get update && apt-get install -y \
    libexpat1 \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install uv
RUN pip install --no-cache-dir uv

# copy dependency files
COPY pyproject.toml uv.lock ./

# install python deps
RUN uv sync --frozen

# copy backend code
COPY Backend ./Backend

EXPOSE 8000

ENV DATA_DIR="/app/Backend/Data/*.tif"
CMD ["uv", "run", "uvicorn", "Backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

