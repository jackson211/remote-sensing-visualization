import sys
import os
from osgeo import gdal, gdalconst
from osgeo.gdalconst import *


class FileNotAnEnviHeader(Exception):
    '''Raised when "ENVI" does not appear on the first line of the file.'''

    def __init__(self, msg):
        msg = 'Failed to parse ENVI header file.'
        super(FileNotAnEnviHeader, self).__init__(msg)


def load_data(file_name, gdal_driver='GTiff'):
    '''
    Converts a GDAL compatable file into a numpy array and associated geodata.
    The rray is provided so you can run with your processing - the geodata consists of the geotransform and gdal dataset object
    If you're using an ENVI binary as input, this willr equire an associated .hdr file otherwise this will fail.
    This needs modifying if you're dealing with multiple bands.

    VARIABLES
    file_name : file name and path of your file

    RETURNS
    image array
    (geotransform, inDs)
    '''
    driver = gdal.GetDriverByName(
        gdal_driver)  # http://www.gdal.org/formats_list.html
    driver.Register()

    inDs = gdal.Open(file_name, GA_ReadOnly)

    if inDs is None:
        print("Couldn't open this file: %s" % (file_name))
        print('/nPerhaps you need an ENVI .hdr file? A quick way to do this is to just open the binary up in ENVI and one will be created for you.')
        sys.exit("Try again!")
    else:
        print("%s opened successfully" % file_name)

    # Extract some info form the inDs
    geotransform = inDs.GetGeoTransform()

    # Get the data as a numpy array
    band_num = inDs.RasterCount

    return (band_num, geotransform, inDs)


def read_img_array(inDs, band_id):
    band = inDs.GetRasterBand(band_id)
    cols = inDs.RasterXSize
    rows = inDs.RasterYSize
    image_array = band.ReadAsArray(0, 0, cols, rows)
    return image_array


def read_envi_header(file):
    f = open(file, 'r')
    try:
        starts_with_ENVI = f.readline().strip().startswith('ENVI')
    except UnicodeDecodeError:
        msg = 'File does not appear to be an ENVI header (appears to be a ' \
            'binary file).'
        f.close()
        raise FileNotAnEnviHeader(msg)
    else:
        if not starts_with_ENVI:
            msg = 'File does not appear to be an ENVI header (missing "ENVI" \
              at beginning of first line).'
            f.close()
            raise FileNotAnEnviHeader(msg)

    lines = f.readlines()
    f.close()

    dict = {}
    while lines:
        line = lines.pop(0)
        if line.find('=') == -1:
            continue
        if line[0] == ';':
            continue

        (key, sep, val) = line.partition('=')
        key = key.strip()
        if not key.islower():
            key = key.lower()
        val = val.strip()
        if val and val[0] == '{':
            str = val.strip()
            while str[-1] != '}':
                line = lines.pop(0)
                if line[0] == ';':
                    continue

                str += '\n' + line.strip()
            if key == 'description':
                dict[key] = str.strip('{}').strip()
            else:
                vals = str[1:-1].split(',')
                for j in range(len(vals)):
                    vals[j] = vals[j].strip()
                dict[key] = vals
        else:
            dict[key] = val

    return dict


# Usage
# data_dir = "/Users/jackson/Documents/code/bokeh/data"
# file_name = "h20160212_003501_700591"
# hdr_data = os.path.join(data_dir, file_name+".hdr")
# img_data = os.path.join(data_dir, file_name+".img")

# band_num, geodata, raw = load_data(img_data, gdal_driver='GTiff')
# img = read_img_array(raw, 80)
# hdr = read_envi_header(hdr_data)

# print(band_num, geodata)
# print(hdr)
