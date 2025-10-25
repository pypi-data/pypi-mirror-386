#!/usr/bin/env python
import os
import spglib
from .Fourthorder_vasp import fourthorder


spglib_dir = os.path.dirname(spglib.__file__)

LD_LIBRARY_PATH = os.path.join(spglib_dir, "lib64")
os.environ["LD_LIBRARY_PATH"] = LD_LIBRARY_PATH


if __name__ == "__main__":
    fourthorder()
