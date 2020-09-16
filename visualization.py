import numpy as np
import xarray as xr
import holoviews as hv
from holoviews import opts
from holoviews.operation.datashader import regrid, shade
from bokeh.tile_providers import STAMEN_TONER
import panel as pn

import geoviews as gv
import datashader as ds
import cartopy.crs as ccrs
from bokeh.io import output_file, save, show
from bokeh.resources import CDN
from bokeh.embed import file_html


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


def main(path):
    band = read_tiff(path)

    opts.defaults(opts.RGB(width=1024, height=800))

    layout = regrid(combine_bands(
        band) + one_band(band[0]) + one_band(band[1])+one_band(band[2])).redim(x='Longitude', y='Latitude')
    layout.opts(
        opts.RGB(width=600, height=468, framewise=True)).cols(2)

    # Build panel
    tabs = pn.Tabs(("Raster Image Channels", layout))
    tabs.extend([('Some', pn.widgets.FloatSlider()),
                 ('Random', pn.widgets.TextInput()),
                 ('Shit', pn.widgets.ColorPicker())
                 ])

    pn_column = pn.Column(pn.pane.Markdown(
        '# Remote Sensing Image Viewer', style={'font-family': "Gill Sans"}), tabs)

    pn.panel(pn_column).show(title='Remote Sensing')


if __name__ == "__main__":
    file_path = '/Users/jackson/Documents/code/bokeh/data/rgb20200810_093400_372485_geotiff.tif'
    main(file_path)
