#!/usr/bin/env python
import paths # make sure this is the first import!
from benchmark.testcase_generator import create_input_tc1
from benchmark.csv_framework import Datafile, write_sets
from util.irange import irange
from data_structures import *
import math

xrange = [1e0, 1e3]
npoints = 120
exp = math.pow(xrange[1]-xrange[0], 1/float(npoints))
input_data = Datafile('inputs.txt', mode='write')

pid = 1
for ncs in [3]:
    ncomps = map(lambda x: math.pow(exp,x), irange(0, npoints))     # create exponentially spaced x values
    ncomps = sorted(set(map(lambda x: int(math.ceil(x)), ncomps)))  # round up and remove duplicates
    ncomps = filter(lambda x: x >= ncs, ncomps)                     # filter |COMP| >= |SCS|
    for ncomp in ncomps:
        input = create_input_tc1(ncomp, ncs)
        p = Problem(pid=pid, ncs=ncs, ncomp=ncomp, neffcs=len(input))
        print p, write_sets(input)
        input_data.appendline(write_sets(input))
        pid += 1

Problem.save()