# G-code Scaling Script

This Python script scales the X, Y, and Z coordinates in a G-code file by specified factors and exports the scaled G-code to a new file.

## Features

- Scale G-code coordinates for X, Y, and Z axes independently. (also scales I, J, K respectively for arc centers)
- A default output file name is derived based on the input file and scaling factors.
- Optionally an arbitrary output file name can be specified.

## Requirements

- Python 3.x

## Usage
Scale an input G-code file with default scaling factors and generate a default output file name.

```sh
python scale_gcode.py input.gcode -x 1.5 -y 1.2 -z 1.0
```

```sh
python scale_gcode.py another_input.nc -x 0.5 -y 0.5 -o scaled.nc
```

### Command Line Arguments

- `input_file`: Path to the input G-code file (required).
- `-o`: Path to the output scaled G-code file (optional). If not provided, a default filename will be generated.
- `-x`: Scaling factor for X axis. Default is 1.0.
- `-y`: Scaling factor for Y axis. Default is 1.0.
- `-z`: Scaling factor for Z axis. Default is 1.0.
