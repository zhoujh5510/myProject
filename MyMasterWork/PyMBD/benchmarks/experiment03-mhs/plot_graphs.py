#!/usr/bin/env python
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from data_structures import *
from pymbd.benchmark.csv_framework import *
from collections import defaultdict
from glob import glob
import subprocess
import csv
import argparse
import os

default_run_id      = "run01"
parser = argparse.ArgumentParser(description='Create graphs for MHS experiment')
parser.add_argument('-r', '--run', metavar='ID', type=str, default=default_run_id, dest='run_id', 
                    help='use ID as run identifier (default: %s)' % default_run_id)
args = parser.parse_args()
average = lambda l: sum(l)/float(len(l))

os.chdir(args.run_id)
if not os.path.exists('graphs'):
    os.mkdir('graphs')
os.chdir('graphs')

algorithms  = ['hst', 'hsdag', 'saths', 'maxsaths',  
               'bool-it-h1-oldr4', 'bool-it-h1-stop-oldr4', 'bool-it-h1-stop', 'bool-it-h1', 
               'bool-it-h4-oldr4', 'bool-it-h4-stop-oldr4', 'bool-it-h4-stop', 'bool-it-h4', 
               'bool-it-h5-oldr4', 'bool-it-h5-stop-oldr4', 'bool-it-h5-stop', 'bool-it-h5', 
               'bool-rec-h1-oldr4', 'bool-rec-h1-stop-oldr4', 'bool-rec-h1-stop', 'bool-rec-h1', 
               'bool-rec-h4-oldr4', 'bool-rec-h4-stop-oldr4', 'bool-rec-h4-stop', 'bool-rec-h4', 
               'bool-rec-h5-oldr4', 'bool-rec-h5-stop-oldr4', 'bool-rec-h5-stop', 'bool-rec-h5']

for a in algorithms:
    filename = '../results-%s.txt' % a
    if os.path.exists(filename):
        Result.read(filename)
        rs = defaultdict(list)
        for r in  Result.objects:
            rs[r.pid] += [r]
        
        comp_exectime = map(lambda pid: (rs[pid][0].ncomp, average(map(lambda r: r.total_time, rs[pid])), average(map(lambda r: r.max_rss, rs[pid]))), rs)
        csv.writer(open('data-%s.txt'%a, 'w'), dialect='table').writerows(comp_exectime)

for gp in glob('*.gp'):
    subprocess.call(['gnuplot', gp])
    
for tex in glob('*.tex'):
    subprocess.call(['pdflatex', tex])

for tmp in glob('*.tex') + glob("*.log") + glob("*.aux") + glob("*.eps") + glob("*-converted-to.pdf"):
    os.remove(tmp)
    
