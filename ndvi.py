import matplotlib.pyplot as plt
import envi_reader as es
import numpy as np
import os
import cv2

data_dir = "/Users/jackson/Documents/code/bokeh/data"
file_name = "20160212_003501_700591"
hdr_path = os.path.join(data_dir, "h"+file_name+".hdr")
# img_path = os.path.join(data_dir, "h"+file_name+".img")
npy_path = os.path.join(data_dir, "h"+file_name+".npy")

# band_num, geodata, raw = es.load_raw(img_path)
data = np.load(npy_path)
hdr = es.read_envi_header(hdr_path)

wavelengths = [float(i) for i in hdr['wavelength']]


band_width = wavelengths[1] - wavelengths[0]

nir_band_num = 55
red_band_num = 95
band_nums = [nir_band_num, red_band_num]
for band_num in band_nums:
    print(f'band {band_num} wavelength range: ' +
          str(round(wavelengths[band_num]-band_width/2, 2)) + '-' + str(round(wavelengths[band_num]+band_width/2, 2)) + ' nm')

band_nir = data[nir_band_num]
band_red = data[red_band_num]

# Allow division by zero
np.seterr(divide='ignore', invalid='ignore')

# Calculate NDVI
ndvi = np.divide((band_nir-band_red), (band_nir+band_red))


cmap = plt.cm.nipy_spectral

fig, ax = plt.subplots(1, 1, figsize=(5, 5))
ax.imshow(ndvi, cmap=cmap)
plt.show()

print(np.nanmin(ndvi))
norm = plt.Normalize(vmin=np.nanmin(ndvi), vmax=np.nanmax(ndvi))
image = cmap(norm(ndvi))
plt.imsave('test.png', image, cmap=cmap)
