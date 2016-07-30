#!/usr/bin/env python
#
# computes a single benchmark example with given parameters on-the-fly using the theorem prover
# usage:./compute_single.py <algorithm-name> <max-cardinality> <prune> <max-time> <use-old-oracle-spec>
#   e.g../compute_single.py greiner 3 True 330 False
# the problem input (specification) is read from stdin. after the computation, stdout gives the result (SHS) 
# on the first output line, and execution statistics on the second line
import os
import sys
import time
import signal
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from pymbd.benchmark.csv_framework import write_sets
from oracle import IscasOracle, IscasOracleOld
from pymbd.diagnosis.problem import Problem
from pymbd.util.sethelper import minimize_sets

sys.setrecursionlimit(2**16)
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
prune     = bool(sys.argv[3])
max_time  = int(sys.argv[4])

input = sys.stdin.readline().strip()
spec = eval(input)
if len(sys.argv) > 5 and bool(sys.argv[5]):
    description = IscasOracleOld(*spec)
else:
    description = IscasOracle(*spec)

try:
    p = Problem()
    result = p.compute_with_description(description, algorithm, prune=prune, max_time=max_time, max_card=max_card)
    hs = result.get_diagnoses()
    stats = result.get_stats()
    stats['num_hs'] = len(hs)
    stats['num_cs'] = len(description.scs)
    stats['num_min_cs'] = len(minimize_sets(description.scs))

    signal.signal(signal.SIGHUP,  signal.SIG_IGN)
    signal.signal(signal.SIGINT,  signal.SIG_IGN)
    signal.signal(signal.SIGALRM, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    try:
        stats['num_vars'] = description.net.comp_problem.engine.stats.get('num_vars',0)
    except:
        stats['num_vars'] = 0
    try:
        stats['num_rules'] = description.net.comp_problem.engine.stats.get('num_rules',0)
    except:
        stats['num_rules'] = 0
    print write_sets(hs)
    print str(stats)
    sys.stdout.flush()
    
except IOError:

    import traceback
    traceback.print_exc()
    print "IOError, probably worker proces was killed?"
    print {'total_time':time.time()-begin}
    print
    
