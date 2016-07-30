#!/bin/bash
cd $(dirname -- "$0")
make clean
make
cd python
make clean
make
