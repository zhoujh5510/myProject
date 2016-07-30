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
parser = argparse.ArgumentParser(description='Create graphs for ISCAS experiment.')
parser.add_argument('-r', '--run', metavar='ID', type=str, default=default_run_id, dest='run_id', 
                    help='use ID as run identifier (default: %s)' % default_run_id)
parser.add_argument('-t', '--print-table', action="store_true", dest="print_table", default=False, 
                        help='print timeout-table at the end (default: %s)' % False)
args = parser.parse_args()
average = lambda l: sum(l)/float(len(l))

Problem.read()

os.chdir(args.run_id)
if not os.path.exists('graphs'):
    os.mkdir('graphs')
os.chdir('graphs')

algorithms  = [ 'hsdag-cache-picosat', 'hsdag-cache-yices', 'hsdag-ci-cache-picosat', 
                'hsdag-ci-cache-yices', 'hsdag-ci-picosat', 'hsdag-ci-yices', 'hsdag-picosat', 
                'hsdag-yices', 'hst-cache-picosat', 'hst-cache-yices', 'hst-ci-cache-picosat', 
                'hst-ci-cache-yices', 'hst-ci-picosat', 'hst-ci-yices', 'hst-picosat', 
                'hst-yices' ]

        
def use_in_timeplot(result):
    if 0 < result.total_time <= 300 and result.total_rss > 2048:
        # memout and no timeout -> don't use in time plot
        return False
    else:
        return True

def use_in_memplot(result):
    if 300 < result.total_time and result.total_rss < 2048:
        # timeout and no memout -> don't use for memory plot
        return False
    else:
        return True

timeouts = defaultdict(lambda:defaultdict(lambda:defaultdict(list)))

Result.total_rss = property(lambda self: self.max_rss + self.tp_max_rss)

for a in algorithms:
    filename = '../results-%s.txt' % a
    if os.path.exists(filename):
        Result.read(filename)
        rs = defaultdict(lambda:defaultdict(list))
        for r in  Result.objects:
            rs[r.file][r.max_card] += [r]
        
        n = 0
        
        comp_exectime = []
        for circuit in sorted(rs, lambda x: int(x[1:])):
            for m in [1,2,3]:
                n += 1
                if not rs[circuit][m]:
                    continue
                comp_exectime += [( n, 
                                  average(map(lambda r: 300 if r.total_time > 300 or (r.total_time == 0 and r.max_rss >= 2500) or (r.total_time == 0 and not r.algorithm.startswith("java-") and r.max_rss < 2500) else r.total_time, filter(use_in_timeplot, rs[circuit][m]))),\
                                  min    (map(lambda r: 300 if r.total_time > 300 or (r.total_time == 0 and r.max_rss >= 2500) or (r.total_time == 0 and not r.algorithm.startswith("java-") and r.max_rss < 2500) else r.total_time, filter(use_in_timeplot, rs[circuit][m]))),\
                                  max    (map(lambda r: 300 if r.total_time > 300 or (r.total_time == 0 and r.max_rss >= 2500) or (r.total_time == 0 and not r.algorithm.startswith("java-") and r.max_rss < 2500) else r.total_time, filter(use_in_timeplot, rs[circuit][m]))),\
                                  average(map(lambda r: 2048 if r.total_rss > 2048 else r.total_rss, filter(use_in_memplot, rs[circuit][m]))),\
                                  min    (map(lambda r: 2048 if r.total_rss > 2048 else r.total_rss, filter(use_in_memplot, rs[circuit][m]))),\
                                  max    (map(lambda r: 2048 if r.total_rss > 2048 else r.total_rss, filter(use_in_memplot, rs[circuit][m]))), \
                                  map(lambda r: r.total_time > 300 or (r.total_time == 0 and r.max_rss >= 2500), rs[circuit][m]).count(True), \
                                  map(lambda r: r.total_rss > 2048, rs[circuit][m]).count(True), \
                                  map(lambda r: r.total_rss < 2048 and r.total_time < 300 and (r.total_time > 0 or (r.total_time == 0 and r.total_rss < 2048)), rs[circuit][m]).count(True), \
                                  len(filter(use_in_timeplot, rs[circuit][m])), \
                                  len(filter(use_in_memplot,  rs[circuit][m])), \
                               )]
                for line in comp_exectime:
                    timeouts[circuit][m][a] = [line[7], line[8], line[9]]
                
        csv.writer(open('data-%s.txt'%a, 'w'), dialect='table').writerows(comp_exectime)
	        

if args.print_table:
    print "gates max_card algorithm timeouts memoryouts successful"
    for circuit in timeouts:
        for m in timeouts[circuit]:
            for a in timeouts[circuit][m]:
                print "%s %d" % (circuit, m), 
                for c in timeouts[circuit][m][a]:
                    print c,
                print

    for m in [1,2,3]:
      print  "max_card", m
      for a in sorted(timeouts[880][m], key=lambda x: x):
        print a,
        for g in sorted(map(int,timeouts)):
          print (str(timeouts[g][m][a][0]) if timeouts[g][m][a][0] != 0 else "-") + "/" + (str(timeouts[g][m][a][1]) if timeouts[g][m][a][1] != 0 else "-"),
        print

        
else:

    for gp in glob('*.gp'):
        subprocess.call(['gnuplot', gp])
    
    for tex in glob('*.tex'):
        subprocess.call(['pdflatex', tex])

    for tmp in glob('*.tex') + glob("*.log") + glob("*.aux") + glob("*.eps") + glob("*-converted-to.pdf"):
        os.remove(tmp)
    


