import os
import scipy.io
import argparse
import numpy as np


def mat2npy(filename):
    mat = scipy.io.loadmat(filename)
    data = mat['COD']

    data_dir = os.path.dirname(filename)
    output_file = filename.split('/')[-1].split('.')[0] + '.npy'
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
    input_dir = args.input
    mat2npy(input_dir)
