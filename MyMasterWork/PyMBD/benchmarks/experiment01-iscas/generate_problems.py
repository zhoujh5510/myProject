#!/usr/bin/env python
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from pymbd.benchmark.iscas.testgen import generate_independent_faults
from pymbd.benchmark.iscas.oracle import IscasOracleOld
from pymbd.util.sethelper import powerset
from pymbd.sat.yices import YicesEngine
import traceback
import time

DATA_DIR = '../iscas-data/'
FILES = ['c432.sisc', 'c499.sisc', 'c880.sisc', 'c1355.sisc', 'c1908.sisc', 'c2670.sisc', 'c3540.sisc', 'c5315.sisc', 'c6288.sisc', 'c7552.sisc']
MRANGE = [1,2,3]
TESTS_PER_FILE = 10
OUTPUT_FILE = 'iscas-testcases-%d.txt'

for M in MRANGE:
    with open(OUTPUT_FILE % M, 'w') as output_file: 
        output_file.write("file\tfault\tinputs\toutputs\n")
        for file in FILES:
            success = 0
            tries = 0
            faults = set()
            while success < TESTS_PER_FILE and tries < 100:
                tries += 1  
                try:
                    spec = generate_independent_faults(DATA_DIR + file, M)
                    fault = frozenset([g.output for g in spec[2]])
                    if fault in faults:
                        print "(duplicate created)"
                        continue
                    else:
                        faults.add(fault) 
                    o = IscasOracleOld(*spec)
                    print "%25s %2d %6d" % (file, M, len(o.net.gates)),
                    
                    # instead of computing all hitting sets just check if any subset of `fault' is a hitting set 
                    # if yes -> `fault' cannot be a minimal diagnosis, if no and `fault' is a diagnosis, then it is also 
                    # a minimal diagnosis and we use this example. 
                    minimal = True
                    t0 = time.time()
                    proper_subsets = set(powerset(fault)) - set([frozenset(fault)]) - set([frozenset([])]) # powerset \ full set \ empty set
                    for s in proper_subsets:
                        if o.check_consistency(o.gates_to_numbers(s)):
                            minimal = False
                            break
                    if not o.check_consistency(o.gates_to_numbers(fault)):
                        minimal = False
                    t1 = time.time()
                    print "%12.6f (%d)" % (t1-t0, len(proper_subsets)+1), 
                    
                    if minimal:

                        inputs = ",".join(map(lambda i: "%s=%d" % (i[0],int(i[1])), o.net.inputs.iteritems()))
                        outputs = ",".join(map(lambda i: "%s=%d" % (i[0],int(i[1])), o.net.outputs.iteritems()))    
                        faultd = ",".join(map(lambda i: str(i), fault))                
                        output_file.write("%s\t%s\t%s\t%s\n" % (file[:-5], faultd, inputs, outputs))
                        success += 1
    
                    print minimal
                    o.finished()

                        
                
                except IOError as e:
                    traceback.print_exc()
                    print "\n".join(YicesEngine.yices_in)
                    print "\n".join(YicesEngine.yices_out)
                    break