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

# def display_png(png_file):
#     img = combine_bands(png_file)
#     return img


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


def cod_tap_2(img, cod_data):
    default_x = cod_data.shape[1]/2
    default_y = cod_data.shape[0]/2
    posxy = hv.streams.Tap(source=img, x=default_x, y=default_y)
    print(cod_data.shape)

    def tap_callback(x, y):
        if x > cod_data.shape[1] or x < 0 or y > cod_data.shape[0] or y < 0:
            cod = [0]
        else:
            x = int(x)
            y = int(y)
            cod = cod_data[y, -x]
            print(x, y, cod)
            if np.isnan(cod):
                cod = [0]
        table = hv.Table({'COD': cod}, ['COD'])
        table.opts(height=140)
        return table

    # Create dmap
    dmap = hv.DynamicMap(tap_callback, streams=[posxy])
    dmap.opts(opts.Table(title="COD table"))
    return dmap


def cod_tap(img, cod_data):
    default_x = cod_data.shape[1]/2
    default_y = cod_data.shape[0]/2
    posxy = hv.streams.Tap(source=img, x=default_x, y=default_y)
    print(cod_data.shape)

    def tap_callback(x, y):
        if x > cod_data.shape[1] or x < 0 or y > cod_data.shape[0] or y < 0:
            cod = [0]
        else:
            x = int(x)
            y = int(y)
            cod = cod_data[y, -x]
            print(x, y, cod)
            if np.isnan(cod):
                cod = [0]
        table = hv.Table({'COD': cod}, ['COD'])
        table.opts(height=140)
        return table

    # Create dmap
    dmap = hv.DynamicMap(tap_callback, streams=[posxy])
    dmap.opts(opts.Table(title="COD table"))
    return dmap


def display(file_name, data, hdr, tiff, ndvi_file, river1_file, river1_data, river2_file, river2_data, large_img):
    wavelength = [float(i) for i in hdr['wavelength']]

    # Init tab component
    tabs = pn.Tabs()

    # Title
    title = pn.Row(pn.pane.Markdown("#Remote Sensing Image Viewer", style={'font-family': 'helvetica'},
                                    width_policy='max', height=50, sizing_mode='stretch_width', css_classes=['title']))

    # Main images
    tiff_img = combine_bands(tiff)
    tiff_img.opts(opts.RGB(title=f"Data: {file_name}", width=800, height=624, framewise=True,
                           bgcolor='black', tools=['hover', 'tap', crosshair]))
    tap_combined = image_tap(tiff_img, data, wavelength)
    tabs.append(('Spectral Curve', pn.Row(tiff_img, tap_combined)))

    # NDVI tab
    ndvi_img = combine_bands(ndvi_file)
    ndvi_img.opts(opts.RGB(title="NDVI", width=800, height=624, framewise=True,
                           bgcolor='black', tools=['hover', 'tap', crosshair]))
    tabs.append(('NDVI', ndvi_img))

    # River 1 tab
    river1_img = combine_bands(river1_file)
    river1_img.opts(opts.RGB(title="River", width=800, height=800, framewise=True,
                             bgcolor='black', tools=['hover', 'tap', crosshair]))
    river1_cod_combined = cod_tap(river1_img, river1_data)
    tabs.append(('云南 River 1', pn.Row(river1_img, river1_cod_combined)))

    # River 2 tab
    river2_img = combine_bands(river2_file)
    river2_img.opts(opts.RGB(title="River", width=800, height=669, framewise=True,
                             bgcolor='black', tools=['hover', 'tap', crosshair]))
    river2_cod_combined = cod_tap_2(river2_img, river2_data)
    tabs.append(('云南 River 2', pn.Row(river2_img, river2_cod_combined)))

    # Large Image tab
    large = combine_bands(large_img)
    large.opts(opts.RGB(title="南通", width=900, height=600, framewise=True,
                        bgcolor='white', tools=['hover', 'tap', crosshair]))
    tabs.append(('南通', pn.Row(large)))

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


# Note: no if __name__ == "__main__": for panel server
# if __name__ == "__main__":
# parser = argparse.ArgumentParser()
# parser.add_argument("-i",
#                     "--input",
#                     type=str,
#                     required=True,
#                     help="Input tiff image")
# args = parser.parse_args()
# input_dir = args.input


input_dir = "data/rgb20160212_003501_700591.tif"
ndvi_img_path = "data/ndvi.png"

river1_img_path = "data/yunnan/river1_rgb.png"
river1_cod_path = "data/yunnan/river1_COD.npy"
river2_img_path = "data/yunnan/river2_RGB.png"
river2_cod_path = "data/yunnan/river2_COD.npy"
large_img_path = "data/nantong/river1_rgb.png"


ndvi_file = read_tiff(ndvi_img_path)
river1_file = read_tiff(river1_img_path)
river1_data = np.load(river1_cod_path)
river2_file = read_tiff(river2_img_path)
river2_data = np.load(river1_cod_path)
large_img = read_tiff(large_img_path)


file_name, tiff_path, hdr_path, npy_path = path_parser(input_dir)
data, hdr, tiff = load_data(tiff_path, hdr_path, npy_path)


app = display(file_name, data, hdr, tiff, ndvi_file,
              river1_file, river1_data, river2_file, river2_data, large_img)
app.servable(title='Remote Sensing')
