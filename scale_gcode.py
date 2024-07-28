"""
This script scales a G-code file by specified factors for each axis.
"""

__author__ = "Andreas  Ennemoser"
__version__ = "1.0.0"
__date__ = "2024-07-28"
__license__ = "MIT"


import argparse
import re
import os

def scale_gcode(input_file, output_file, scale_factors):
    """
    Scale the G-code file by specified factors for each axis.

    :param input_file: Path to the input G-code file.
    :param output_file: Path to the output scaled G-code file.
    :param scale_factors: Dictionary containing scale factors for 'x', 'y', and 'z' axes.
    """
    with open(input_file, 'r') as file:
        lines = file.readlines()
    
    scaled_lines = []
    for line in lines:
        scaled_line = line
        for axis in ['X', 'Y', 'Z']:
            match = re.search(f"{axis}([-+]?[0-9]*\.?[0-9]+)", line)
            if match:
                original_value = float(match.group(1))
                scaled_value = original_value * scale_factors[axis.lower()]
                scaled_line = scaled_line.replace(match.group(0), f"{axis}{scaled_value:.4f}")
        scaled_lines.append(scaled_line)

    with open(output_file, 'w') as file:
        file.writelines(scaled_lines)

def create_default_output_filename(input_file, scale_factors):
    """
    Create a default output filename based on the input filename and scale factors.

    :param input_file: Path to the input G-code file.
    :param scale_factors: Dictionary containing scale factors for 'x', 'y', and 'z' axes.
    :return: Generated output filename.
    """
    base_name, ext = os.path.splitext(input_file)
    scale_str = "_".join([f"{axis}{str(scale_factors[axis]).replace('.', 'c')}" for axis in scale_factors])
    return f"{base_name}_scaled_{scale_str}{ext}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scale a G-code file by specified factors for each axis.")
    parser.add_argument("input_file", help="Path to the input G-code file.")
    parser.add_argument("-o", help="Path to the output scaled G-code file. If not provided, a default filename will be generated.")
    parser.add_argument("-x", type=float, default=1.0, help="Scaling factor for X axis. Default is 1.0")
    parser.add_argument("-y", type=float, default=1.0, help="Scaling factor for Y axis. Default is 1.0")
    parser.add_argument("-z", type=float, default=1.0, help="Scaling factor for Z axis. Default is 1.0")

    args = parser.parse_args()

    scale_factors = {'x': args.x, 'y': args.y, 'z': args.z}

    if args.o:
        output_file = args.o
    else:
        output_file = create_default_output_filename(args.input_file, scale_factors)

    scale_gcode(args.input_file, output_file, scale_factors)
    print(f"Scaled G-code has been saved to {output_file}")

