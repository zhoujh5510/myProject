#!/usr/bin/env python
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from data_structures import *
from pymbd.benchmark.csv_framework import Datafile
from pymbd.benchmark.ltl.generator import generate_mutated_formula_and_witness
from pymbd.benchmark.ltl.ltlparser.ast import Identifier, get_all_subformulas, Type
from pymbd.benchmark.ltl.ltlparser.rewriting import rewrite_to_dag
from itertools import islice
from pymbd.util.irange import irange
import math
import argparse


parser = argparse.ArgumentParser(description='Compute problems')
modes = parser.add_mutually_exclusive_group()
modes.add_argument('-f', '--full-recompute', action='store_true', dest='recompute', default=True, 
                   help='redo the whole computation run (default)')
modes.add_argument('-c', '--continue', action='store_false', dest='recompute', 
                   help='finish an unfinished computation run')
args = parser.parse_args()

vrange = [1e0, 1e3]
npoints = 60
exp = math.pow(vrange[1]-vrange[0], 1/float(npoints))
lengths = map(lambda x: math.pow(exp,x), irange(0, npoints))     # create exponentially spaced x values
lengths = sorted(set(map(lambda x: int(math.ceil(x)), lengths)))  # round up and remove duplicates
lengths = filter(lambda x: x >= 3, lengths)                      # less than 3 doesn't make sense


num_faults      = 1
sample_size     = 10
trace_size      = 100
trace_stem_size = 50

samples = xrange(sample_size)
Task = makestruct('Task', 'length sample')
tasks = (Task(length=l, sample=s) for l in lengths for s in samples)

if args.recompute:
    input_data = Datafile('inputs.txt', mode='write')
    pid = 1
else:
    input_data = Datafile("inputs.txt", mode='append')
    Problem.read()
    pid = Problem.objects[-1].pid
    tasks = islice(tasks, pid, None)
    pid += 1

for t in tasks:
    r = generate_mutated_formula_and_witness(formula_args=[t.length, math.floor(t.length/3), 0.5, False, False, set()],  trace_length=(trace_size,trace_stem_size), num_faults=num_faults)
    if r is not None:
        f, ff, t = r
        ff = rewrite_to_dag(ff)
        vars = map(lambda i: Identifier(i), set(map(str,get_all_subformulas(ff, Type.Identifier))))
        print 
        print "%3d " % pid + str(ff).ljust(70),
        Problem(pid=pid, specid=pid, specsize=len(ff), specnumvars=len(vars), tracesize=trace_size, tracestemsize=trace_stem_size, num_faults=num_faults)
        input_data.appendline(str(pid) + "\t" + str(ff) + "\t" + str(f) + "\t" + str(t))
        Problem.save()
        pid += 1

