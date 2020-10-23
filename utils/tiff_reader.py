import rasterio
import numpy as np

file = "/Users/jackson/Documents/code/bokeh/remote-sensing-visualization/620.tif"

data = rasterio.open(file)
data_meta = data.meta
print(data_meta)

all_bands = []
for name in data.subdatasets:
    print(name)
    with rasterio.open(name) as f:
        all_bands.append(f.read(1))

stacked_all_bands = np.stack(all_bands)
print(stacked_all_bands.shape)

# data_meta.update(count=len(all_bands))

# Read each layer and write it to stack
# with rasterio.open('stack.tif', 'w', **data_meta) as dst:
#     for id, layer in enumerate(all_bands, start=1):
#         with rasterio.open(layer) as src1:
#             dst.write_band(id, src1.read(1))
