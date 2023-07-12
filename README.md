# Description

This project interfaces with a Red Pitaya SCPI server. 

# Installation

To install this project, make sure you have installed the `build` package in your python distribution. Namely, run `pip install build`. We will use this package to help us interpret the `pyproject.toml` file which specifies our build.
After installing the `build` package, run `python -m build` in this directory, which contains the `pyproject.toml` file. This should produce a `dist` directory, which contains both a Python wheel and a packaged tarball with our code.
Install the python wheel with `pip install [NAME OF WHEEL FILE]`. For me, this ended up being `pip install rpnacs-0.0.1-py3-none-any.whl`. Now, you should be ready to import files from this package using statements like `from rpnacs.lib import scope`

# Included Projects

Included at the moment is a `pyqt5` based GUI for remote laser locking. It is poorly named `test_gui.py` at the moment and is located in the `test` folder.
