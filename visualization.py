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
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.plotting import figure


nodata = 1

css = '''
.title {
    font-family: Helvetica,
    font-weight: bold,
    color: black
}
'''

pn.extension(raw_css=[css])


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

    # Combing images
    layout = regrid(combine_bands(
        band) + one_band(band[0]) + one_band(band[1])+one_band(band[2])).redim(x='Longitude', y='Latitude')
    layout.opts(
        opts.RGB(width=600, height=468, framewise=True)).cols(2)

    # Figure
    p1 = figure(width=300, height=300)
    p1.line([1, 2, 3], [1, 2, 3])

    # Build panel
    tabs = pn.Tabs(("Raster Image Channels", layout))
    tabs.extend([('Some', p1),
                 ('Random', pn.widgets.TextInput()),
                 ('Shit', pn.widgets.ColorPicker())
                 ])

    # Grid layout
    gspec = pn.GridSpec(sizing_mode='stretch_width',
                        max_width=600, height=100)

    gspec[0, 0] = pn.Spacer(margin=0)
    gspec[0, 1:6] = pn.Row('# Remote Sensing Image Viewer',
                           margin=(0, 0, 10, 0), css_classes=['title'])
    gspec[0, 6] = pn.Spacer(margin=0)
    gspec[1, 1:6] = tabs
    # print(gspec.grid)
    gspec.show(title='Remote Sensing')


if __name__ == "__main__":
    file_path = '/Users/jackson/Documents/code/bokeh/data/rgb20200810_093400_372485_geotiff.tif'
    main(file_path)
