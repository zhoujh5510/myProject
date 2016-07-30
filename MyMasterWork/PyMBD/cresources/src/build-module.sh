#!/bin/bash
cd "$(dirname -- "$0")/c_algorithm"
rm -f _c_algorithm.so
/usr/bin/env python setup.py build_ext --inplace
