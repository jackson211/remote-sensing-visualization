import os
import numpy as np
import argparse
import envi_reader as es


def main(input_path):
    print(f"Reading img file from {input_path}")
    band_num, geodata, data = es.load_raw(input_path, gdal_driver='GTiff')
    data_dir = os.path.dirname(input_path)
    output_file = input_path.split('/')[-1].split('.')[0] + '.npy'
    output_path = os.path.join(data_dir, output_file)
    print(f"Saving npy to {output_path}")
    np.save(output_path, data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i",
                        "--input",
                        type=str,
                        required=True,
                        help="Input tiff image")
    args = parser.parse_args()
    main(args.input)
