# MHFU/P3rd PMO Exporter

## Overview

Blender 3.6 addon to export models for the games Monster Hunter Freedom
Unite and Monster Hunter Portable 3rd for the Sony PSP console.

## Installation

PyFFI must be installed on your Blender python installation
this can be done by running the following command. ("python" must be 
your blender python interpreter).

```commandline
python -m install pyffi
```

alternative you can run this in Blender's python console

```python
import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "pyffi"])
```

## Usage

You can get a clue on how to use this with this [pretty bad tutorial](https://youtu.be/qGSAnYVDiW0).

## Known bugs

Monster models for MHP3rd are not working.

## Credits

To [Seth VanHeulen](https://gitlab.com/svanheulen/) [(mhfz)](https://gitlab.com/svanheulen/mhff) and [*&](https://github.com/AsteriskAmpersand) [(PMO Importer)](https://github.com/AsteriskAmpersand/PMO-Importer) for their research and documentation on the format. To [codestation](https://github.com/codestation) for [mhtools](https://github.com/codestation/mhtools).
And CAPCOM, for making the games.

Special thanks to [IncognitoMan](https://github.com/IncognitoMan) for giving some inspiration for this, without him asking about it, probably MHFU support wouldn't be a thing.