import matplotlib.pyplot as plt
import os
import re
import argparse
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

hv.extension('bokeh', logo=False)

nodata = 1
crosshair = CrosshairTool(
    dimensions="both", line_width=3, line_color="#66FF99", line_alpha=0.8)


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
    if len(band) == 3:
        r, g, b = [ds.utils.orient_array(img) for img in band]
        a = (np.where(np.logical_or(np.isnan(r), r <= nodata), 0, 255)).astype(np.uint8)
    elif len(band) == 4:
        r, g, b, a = [ds.utils.orient_array(img) for img in band]
    else:
        return None
    return hv.RGB((xs, ys[::-1], r, g, b, a), kdims=['X', 'Y'], vdims=list('RGBA'))


def image_tap(img, data, wavelength):
    default_x = data.shape[2]/2
    default_y = data.shape[1]/2
    posxy = hv.streams.Tap(source=img, x=default_x, y=default_y)
    curve_dict = {}

    def create_curve(x, y):
        spectral_curve = data[:, -int(y), int(x)]
        curve = hv.Curve((wavelength, spectral_curve))
        return curve

    def tap_callback(x, y):
        x = int(x)
        y = int(y)
        if x == -1 and y == -1:
            x = int(default_x)
            y = int(default_y)
        curve_dict[(x, y)] = create_curve(x, y)
        return hv.NdOverlay(curve_dict, kdims=['X', 'Y'])

    # Create dmap
    dmap = hv.DynamicMap(tap_callback, streams=[posxy])
    spikes = hv.Spikes(wavelength)
    layout = dmap + spikes
    layout.opts(opts.Curve(title="Spectral Curve", xaxis=None, ylabel='DN Value',  height=380, width=600, tools=[
                'hover', crosshair]), opts.Spikes(height=120, width=600, xlabel='Wavelength(nm)', yaxis=None, line_width=0.5, color='grey')).cols(1)

    # button
    def clear(event):
        curve_dict.clear()
        dmap.event(x=-1, y=-1)
    button = pn.widgets.Button(name='Clear', button_type='danger')
    button.on_click(clear)
    return pn.Column(layout, button)


def ndvi(ndvi_file):
    img = regrid(combine_bands(ndvi_file))
    img.opts(opts.RGB(title=f"ndvi", width=800, height=624, framewise=True,
                      bgcolor='black', tools=['hover', 'tap', crosshair]))
    return img


def display(file_name, data, hdr, tiff, ndvi_file):
    wavelength = [float(i) for i in hdr['wavelength']]

    # Combing images
    combined = combine_bands(tiff)
    image_layout = regrid(combined)
    image_layout.opts(opts.RGB(title=f"Data: {file_name}", width=800, height=624, framewise=True,
                               bgcolor='black', tools=['hover', 'tap', crosshair]))

    tap_combined = image_tap(combined, data, wavelength)
    title = pn.Row(pn.pane.Markdown("#Remote Sensing Image Viewer", style={'font-family': 'helvetica'},
                                    width_policy='max', height=50, sizing_mode='stretch_width', css_classes=['title']))

    tabs = pn.Tabs(('Spectral Curve', pn.Row(
        image_layout, tap_combined)))

    ndvi_img = ndvi(ndvi_file)
    tabs.append(ndvi_img)

    container = pn.Column(title, tabs, sizing_mode='stretch_both')
    return container


def path_parser(input_dir):
    # Parse file path
    data_dir = os.path.dirname(input_dir)
    file_name = os.path.basename(input_dir).split('.')[0]
    if file_name[:1].isalpha():
        file_name = re.sub(r'^[a-zA-Z]*', '', file_name)

    tiff_path = os.path.join(data_dir, "rgb"+file_name+".tif")
    hdr_path = os.path.join(data_dir, "h"+file_name+".hdr")
    npy_path = os.path.join(data_dir, "h"+file_name+".npy")
    print(f"Reading file from {tiff_path}, {hdr_path}, {npy_path}")
    return (file_name, tiff_path, hdr_path, npy_path)


def load_data(tiff_path, hdr_path, npy_path, bit_16=True):
    data = np.load(npy_path)
    hdr = es.read_envi_header(hdr_path)
    tiff = read_tiff(tiff_path)
    if bit_16:
        tiff = (tiff/256).astype(np.uint8)  # for 16bit TIFF
    return (data, hdr, tiff)


# if __name__ == "__main__":
# parser = argparse.ArgumentParser()
# parser.add_argument("-i",
#                     "--input",
#                     type=str,
#                     required=True,
#                     help="Input tiff image")
# args = parser.parse_args()
# input_dir = args.input

input_dir = "../data/rgb20160212_003501_700591.tif"
ndvi_path = "../data/ndvi.png"
ndvi_file = read_tiff(ndvi_path)

file_name, tiff_path, hdr_path, npy_path = path_parser(input_dir)
data, hdr, tiff = load_data(tiff_path, hdr_path, npy_path)


app = display(file_name, data, hdr, tiff, ndvi_file)
app.servable(title='Remote Sensing')
