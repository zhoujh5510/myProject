#!/usr/bin/env python
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from data_structures import *
from pymbd.benchmark.csv_framework import *
from collections import defaultdict
from itertools import takewhile
from glob import glob
import subprocess
import csv
import argparse
import os

default_run_id      = "run01"
parser = argparse.ArgumentParser(description='Create graphs.')
parser.add_argument('-r', '--run', metavar='ID', type=str, default=default_run_id, dest='run_id', 
                    help='use ID as run identifier (default: %s)' % default_run_id)
parser.add_argument('-t', '--print-table', action="store_true", dest="print_table", default=False, 
                        help='print timeout-table at the end (default: %s)' % False)
args = parser.parse_args()
average = lambda l: sum(l)/float(len(l))

print args.run_id

os.chdir(args.run_id)
if not os.path.exists('graphs'):
    os.mkdir('graphs')
os.chdir('graphs')

algorithms  = ['hsdag-fm-cache', 'hsdag-ci-fm-cache', 'hsdag-cache-picosat', 
               'hsdag-ci-cache-picosat']

timeouts = defaultdict(lambda:defaultdict(lambda:defaultdict(list)))

first_n = 10
Result.aborted = lambda self: self.total_time > 300 or self.timeout or self.max_rss > 2048 or self.memout

for c in [1,2,3]:
    for a in algorithms:
        filename = '../results-%s.txt' % a
        output_filename = '../output-%s.txt' % a
        if os.path.exists(filename):
            print "   ", a, c
            Result.read(filename)
            datafile = Datafile(output_filename)
            rs = defaultdict(list)
            for i, r in  enumerate(Result.objects, 1):
                r.rownum = i
                if r.max_card == c:

                    output = datafile.getline(r.rownum).split("\t",2)
                    try:
                        output_pid = int(output[1])
                    except:
                        print output_filename, r.rownum, output
                    if output_pid != r.pid:
                        raise Exception("Something's wrong in the output file, expected pid %d on line %d but found %d" % (r.pid, r.rownum, output_pid))
                    # print
                    # print output

                    # print output[2].split(",\t")[:-1]
                    try:
                        output_line = output[2][:-1] if output[2][-1] == "," else output[2]
                        diagnoses = dict(map(lambda x: (x[0].strip(), float(x[1])), map(lambda x: x.split(" : "), output[2].split(",")[:-1])))
                    except:
                        # print output_filename, r.rownum, output
                        diagnoses = dict()
                    # diagnoses = dict(map(lambda x: (x[0].strip(), float(x[1])), map(lambda x: x.split(" : "), output_line.split(",\t"))))
                    
                    # print diagnoses

                    times = sorted(diagnoses.values())
                    r.time_for_first_n = times[:first_n][-1] if times else 0
                    r.considered_diagnoses = len(times[:first_n]) if r.aborted() else first_n
                    r.real_first_n_diagnoses = len(times[:first_n])

                    rs[r.specsize] += [r]

            cs_exectime = map(lambda id: (  rs[id][0].specsize,                                                 # 0: formula size
                                            average(map(lambda r: r.total_time, rs[id])),                 # 1: total time
                                            average(map(lambda r: r.first_timestamp, rs[id])),            # 2: time for first diagnosis
                                            average(map(lambda r: r.max_rss, rs[id])),                    # 3: algorithm max.RSS
                                            average(map(lambda r: r.sat_max_rss, rs[id])),                # 4: sat solver max.RSS
                                            map(lambda r: r.total_time > 300 or r.timeout, rs[id]).count(True), # 5: number of timeouts
                                            map(lambda r: r.max_rss > 2048 or r.memout, rs[id]).count(True),    # 6: number of memouts
                                            len(rs[id]),                                                        # 7: number of samples
                                            average(map(lambda r: r.time_for_first_n, rs[id])),           # 8: time for first X (10) diagnoses
                                            sum(map(lambda r: r.considered_diagnoses, rs[id])),                 # 9: should be samples * first_n
                                            min    (map(lambda r: r.real_first_n_diagnoses, rs[id])),     # 10: min number of really found diagnoses within X 
                                            average(map(lambda r: r.real_first_n_diagnoses, rs[id])),     # 11: avg of 10
                                            max    (map(lambda r: r.real_first_n_diagnoses, rs[id])),     # 12: max of 10
                                            min    (map(lambda r: r.num_hs, rs[id])),                     # 13: min number of total diagnoses
                                            average(map(lambda r: r.num_hs, rs[id])),                     # 14: avg number of total diagnoses
                                            max    (map(lambda r: r.num_hs, rs[id])),                     # 15: max number of total diagnoses
                          ), rs)
            
            
            cs_exectime = sorted(cs_exectime, key=lambda e: e[0])

            
            cs_exectime = list(takewhile(lambda t: t[5] == 0, cs_exectime)) # as long as no timeouts
            # print cs_exectime
            for t in cs_exectime:
                timeouts[c][a][t[0]] = [t[5], t[6], t[7]]
        
            if cs_exectime:
                csv.writer(open('data-%s-%d.txt'%(a,c), 'w'), dialect='table').writerows(cs_exectime)
        # else:
            # print "skipping %s" % a

if args.print_table:
    for c in timeouts:
        for a in timeouts[c]:
            for specsize in timeouts[c][a]:
                s = timeouts[c][a][specsize]
                print "%d %s %d %d %d %d" % (c, a, specsize, s[0], s[1], s[2]) 
else:
    for gp in glob('*.gp'):
        subprocess.call(['gnuplot', gp])
        
    for tex in glob('*.tex'):
        subprocess.call(['pdflatex', tex])

for tmp in glob('*.tex') + glob("*.log") + glob("*.aux") + glob("*.eps") + glob("*-converted-to.pdf"):
    os.remove(tmp)
    
