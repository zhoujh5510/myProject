#!/usr/bin/env python
#
# important! keep these sys.path.append lines before any non standard-python imports
import os
import sys
import time
import signal
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from pymbd.benchmark.csv_framework import write_sets
from pymbd.diagnosis.problem import Problem
from pymbd.benchmark.ltl.ltlparser.parser import parse
from pymbd.benchmark.ltl.ltlparser.rewriting import  rewrite_spec
from pymbd.benchmark.ltl.encoding.oracles import FaultModeConflictSetHittingSetDescription, SimpleHittingSetDescription


begin = time.time()

def terminate(signum, frame):
    print ""
    #if signum == signal.SIGINT:
    #    print {'total_time':time.time()-begin}
    #else:
    print {'total_time':time.time()-begin}
    print
    sys.stdout.flush()
    sys.exit()
    
signal.signal(signal.SIGHUP,  terminate)
signal.signal(signal.SIGINT,  terminate)
signal.signal(signal.SIGALRM, terminate)
signal.signal(signal.SIGTERM, terminate)

    
algorithm = str(sys.argv[1])
max_card  = int(sys.argv[2])
max_time  = int(sys.argv[3])
mode      = "strong"
opts      = {}
if len(sys.argv) > 4:
    mode = sys.argv[4]
if len(sys.argv) > 5:
    opts = eval(sys.argv[5])
    
spec,trace = sys.stdin.readlines()[:2]
f = parse(spec)
t = parse(trace)

if mode == "strong":
    description = FaultModeConflictSetHittingSetDescription(f, t, **opts)
else:
    description = SimpleHittingSetDescription(f, t, **opts)
    
p = Problem()
result = p.compute_with_description(description, algorithm, max_time=max_time, max_card=max_card)

signal.signal(signal.SIGHUP,  signal.SIG_IGN)
signal.signal(signal.SIGINT,  signal.SIG_IGN)
signal.signal(signal.SIGALRM, signal.SIG_IGN)
signal.signal(signal.SIGTERM, signal.SIG_IGN)

hs = result.get_diagnoses()

stats = result.get_stats()
stats['num_hs'] = len(hs)
stats['num_hs1'] = len(filter(lambda h: len(h) == 1, hs))
stats['num_hs2'] = len(filter(lambda h: len(h) == 2, hs))
stats['num_hs3'] = len(filter(lambda h: len(h) == 3, hs))

if mode == "strong":
    for f,time in stats['time_map'].iteritems():
        print description.hittingset_to_formula(f), ":", str(time) + ",\t",
else:
    for f,time in stats['time_map'].iteritems():
        print map(str, description.numbers_to_nodes(f)), ":", str(time) + ",\t",
    
del stats['time_map']
print
for k,v in description.de.stats.iteritems():
    stats[k if k.startswith("enc_") else "enc_"+k] = v

print str(stats)

print map(list, map(description.nodes_to_numbers, description.scs))

sys.stdout.flush()

