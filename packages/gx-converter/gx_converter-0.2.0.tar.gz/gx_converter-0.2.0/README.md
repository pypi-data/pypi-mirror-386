# GX Converter
Convert .gcode files to the .gx file format for use in FlashForge Adventurer and Monoprice Voxel 3D printers

# Installation

Install via pipx or pip:
~~~sh
pipx install gx-converter
~~~

# Usage

~~~sh
gx-converter FILE.gcode
~~~
You may optionally specify the output file with `--output`, otherwise it will be the same as the input file, 
with a .gx file extension, e.g., FILE.gx.