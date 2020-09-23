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


def tap_callback(x, y):
    print(x, y)
    return hv.Points([x, y])


def main(tiff_path, img_path, hdr_path):
    band_num, geodata, raw = es.load_data(img_path, gdal_driver='GTiff')
    hdr = es.read_envi_header(hdr_path)

    # xs = np.arange(raw.RasterXSize)
    # ys = np.arange(raw.RasterYSize)

    # r = es.read_img_array(raw, 10)
    # g = es.read_img_array(raw, 50)
    # b = es.read_img_array(raw, 80)

    tiff = read_tiff(tiff_path)

    # Combing images
    combined = combine_bands(tiff)
    r = one_band(tiff[0])
    g = one_band(tiff[1])
    b = one_band(tiff[2])

    posxy = hv.streams.Tap(source=combined, x=120.9, y=31.8)
    tap_combined = hv.DynamicMap(tap_callback, streams=[posxy])

    layout = regrid(combined + r + g +
                    b).redim(x='Longitude', y='Latitude')
    layout.opts(
        opts.RGB(width=600, height=468, framewise=True, bgcolor='black', tools=['hover', 'tap'])).cols(2)

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
    img_path = os.path.join(data_dir, "h"+file_name+".img")

    main(tiff_path, img_path, hdr_path)
