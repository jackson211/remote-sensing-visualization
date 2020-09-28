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
from bokeh.models import HoverTool, CrosshairTool
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.plotting import figure

import envi_reader as es

nodata = 1

crosshair = CrosshairTool(
    dimensions="both", line_width=3, line_color="#66FF99", line_alpha=0.8)

# css = '''
# .title {
# font: 1.2em "helvetica", sans-serif;
# }
# '''

# pn.extension(raw_css=[css])


def read_tiff(path):
    return xr.open_rasterio(path).load()


def one_band(b):
    xs, ys = b['x'], b['y']
    b = ds.utils.orient_array(b)
    a = (np.where(np.logical_or(np.isnan(b), b <= nodata), 0, 255)).astype(np.uint8)
    col, rows = b.shape
    return hv.RGB((xs, ys[::-1], b, b, b, a), kdims=['X', 'Y'], vdims=list('RGBA'))


def combine_bands(band):
    xs, ys = band['x'], band['y']
    r, g, b = [ds.utils.orient_array(img) for img in band]
    a = (np.where(np.logical_or(np.isnan(r), r <= nodata), 0, 255)).astype(np.uint8)
    return hv.RGB((xs, ys[::-1], r, g, b, a), kdims=['X', 'Y'], vdims=list('RGBA'))


def image_tap(img, data, wavelength):

    def tap_callback(x, y):
        x = int(x)
        y = int(y)
        spectral_curve = data[:, y, x]
        adj_wave = [(w, s) for s, w in zip(spectral_curve, wavelength)]
        curve = hv.Curve(adj_wave)
        spikes = hv.Spikes(adj_wave)
        layout = curve + spikes
        layout.opts(opts.Curve(title="Spectral Curve at X:" + str(x) +
                               " Y:" + str(y), xaxis=None, height=500, width=600, tools=['hover', crosshair]),
                    opts.Spikes(height=150, width=600, yaxis=None, line_width=0.5, color='grey')).cols(1)
        return layout

    height = data.shape[1]
    width = data.shape[2]
    posxy = hv.streams.Tap(source=img, x=width/2, y=height/2)
    tap_combined = hv.DynamicMap(tap_callback, streams=[posxy])
    return tap_combined


def main(file_name, data, hdr, tiff):
    wavelength = [float(i) for i in hdr['wavelength']]

    # Combing images
    combined = combine_bands(tiff)
    layout = regrid(combined)
    layout.opts(opts.RGB(title=f"Data: {file_name}", width=800, height=624, framewise=True,
                         bgcolor='black', tools=['hover', 'tap', crosshair]))

    tap_combined = image_tap(combined, data, wavelength).redim(
        x='Wavelength(nm)', y='DN Value')
    title = pn.Row(pn.pane.Markdown("#Remote Sensing Image Viewer", style={'font-family': 'helvetica'},
                                    width_policy='max', height=50, sizing_mode='stretch_width', css_classes=['title']))

    container = pn.Column(sizing_mode='stretch_both')
    container.append(title)
    row = pn.Row(layout, tap_combined)
    container.append(row)
    # container.append(tap_combined)
    container.show(title='Remote Sensing')


if __name__ == "__main__":
    data_dir = "/Users/jackson/Documents/code/bokeh/data"
    file_name = "20160212_003501_700591"
    tiff_path = os.path.join(data_dir, "rgb20160212_003501_700591.tif")
    hdr_path = os.path.join(data_dir, "h"+file_name+".hdr")
    npy_path = os.path.join(data_dir, "h"+file_name+".npy")

    data = np.load(npy_path)
    hdr = es.read_envi_header(hdr_path)
    tiff = read_tiff(tiff_path)
    tiff = (tiff/256).astype(np.uint8)  # for 16bit TIFF

    main(file_name, data, hdr, tiff)
