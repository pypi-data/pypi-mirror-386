# gimfu

A toolkit for generating future scenarios in AUTOUGH2.

-----

## Table of Contents

- [Installation](#installation)
- [Commands](#Commands)
- [Related Packages](#related-packages)
- [License](#license)
- [Developer](#Developer)

## Installation

```console
pip install -U gimfu
```

If you use conda, use the supplied `environment.yml` to create `py311-gimfu`.  This installs packages using conda as much as possible before installing packages from PyPI.

```console
conda env create -f environment.yml
```

## Commands

### Make Scenario

To build a scenario from a `.cfg` and its parts (.geners):

```console
make_scenarios make_scenarios_sXXX.cfg
```

This will generate a folder with the scenario name.  Use `run_all_models.bat` for Windows or `./run_all_models.sh`  for Linux/MacOS.

### Convert SAVE file to INCON file

```console
save2incon a.save b.incon
```

NOTE this command is used during the scenario run.

## Related Packages

These packages may be required to generate a full scenario report:
- LaTeX (`latex`, `dvips`)
- gnuplot (`gnuplot`)
- Ghostscript (`gs`)

## License

`gimfu` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## Developer

### Build and Publish

To bump version, create a tag, eg. `v0.1.0`

PyPI token is expected in ~/.pypirc

Publish to PyPI:

```console
hatch build
hatch publish
```

### TODO

- `xlwt` only available in Python <= 3.11 if using conda, replace it with `xlsxwriter`
