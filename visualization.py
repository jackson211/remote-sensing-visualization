import matplotlib.pyplot as plt
import os
import numpy as np
import xarray as xr
import datashader as ds
import cartopy.crs as ccrs

import panel as pn
import geoviews as gv
import holoviews as hv
from holoviews import opts
from holoviews.operation.datashader import regrid, shade
from bokeh.io import output_file, save, show
from bokeh.models import HoverTool
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.plotting import figure

import envi_reader as es

nodata = 1


def read_tiff(path):
    return xr.open_rasterio(path).load()


def one_band(b):
    xs, ys = b['x'], b['y']
    b = ds.utils.orient_array(b)
    a = (np.where(np.logical_or(np.isnan(b), b <= nodata), 0, 255)).astype(np.uint8)
    col, rows = b.shape
    return hv.RGB((xs, ys[::-1], b, b, b, a), vdims=list('RGBA'))


def combine_bands(band):
    xs, ys = band['x'], band['y']
    r, g, b = [ds.utils.orient_array(img) for img in band]
    a = (np.where(np.logical_or(np.isnan(r), r <= nodata), 0, 255)).astype(np.uint8)
    return hv.RGB((xs, ys[::-1], r, g, b, a), vdims=list('RGBA'))


def image_tap(img, data, wavelength):
    def tap_callback(x, y):
        spectral_curve = data[:, int(y), int(x)]
        adj_wave = [(w, s) for s, w in zip(spectral_curve, wavelength)]
        return hv.Curve(adj_wave).opts(title="Spectral Curve", width=500, height=400, tools=['hover'])
    posxy = hv.streams.Tap(source=img, x=1100.9, y=300.8)
    tap_combined = hv.DynamicMap(tap_callback, streams=[posxy])
    return tap_combined


def main(tiff_path, npy_path, hdr_path):
    data = np.load(npy_path)
    hdr = es.read_envi_header(hdr_path)
    wavelength = [float(i) for i in hdr['wavelength']]

    tiff = read_tiff(tiff_path)
    tiff = (tiff/256).astype(np.uint8)

    # Combing images
    combined = combine_bands(tiff)
    layout = regrid(combined).redim(x='X', y='Y')
    layout.opts(opts.RGB(width=600, height=468, framewise=True,
                         bgcolor='black', tools=['hover', 'tap']))

    tap_combined = image_tap(combined, data, wavelength).redim(
        x='Wavelength', y='Value')

    title = pn.panel("""
                                 <div class="title-txt"></div>
                                 # Remote Sensing Image Viewer
                     """)
    cols = pn.Column()
    cols.append(title)
    cols.append(layout)
    cols.append(tap_combined)
    cols.show(title='Remote Sensing')


if __name__ == "__main__":
    # tiff_path = '/Users/jackson/Documents/code/bokeh/data/rgb20200810_093400_372485_geotiff.tif'
    # main(file_path)

    data_dir = "/Users/jackson/Documents/code/bokeh/data"
    file_name = "20160212_003501_700591"
    tiff_path = os.path.join(data_dir, "rgb20160212_003501_700591.tif")
    hdr_path = os.path.join(data_dir, "h"+file_name+".hdr")
    npy_path = os.path.join(data_dir, "h"+file_name+".npy")

    main(tiff_path, npy_path, hdr_path)
