#!/usr/bin/env python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from pymbd.benchmark.csv_framework import *
from pymbd.benchmark.ltl.ltlparser.parser import parse
from pymbd.benchmark.ltl.ltlparser.ast import syntactic_equivalent, get_all_subformulas_list, Type, diff_formulas
from pymbd.util.irange import irange
from data_structures import *
from datetime import datetime
from itertools import dropwhile, ifilter
import signal
import argparse
import gc
import shutil
import re
import time
import traceback

PYTHONPATH = 'python'
THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.setrecursionlimit(2**16)
SOLVER_BACKENDS = {r".*yices.*":"yices", r".*picosat.*":"picosat", r".*scrypto.*":"SCryptoMinisat", r".*":"xxx"}

def compute():
    experiment          = "experiment02"
    default_run_id      = "run01"
    default_sample_size = 1
    timeout_seconds     = 3600
    
    parser = argparse.ArgumentParser(description='Compute problems')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('-f', '--full-recompute', action='store_true', dest='recompute', default=True, 
                       help='redo the whole computation run (default)')
    modes.add_argument('-c', '--continue', action='store_false', dest='recompute', 
                       help='finish an unfinished computation run')
    parser.add_argument('-s', '--samples',  type=int, metavar='S', dest='samples', default=default_sample_size, 
                        help='use S repetitions for each point (default: %d)' % default_sample_size)
    parser.add_argument('-r', '--run', metavar='ID', type=str, default=default_run_id, dest='run_id', 
                        help='use ID as run identifier (default: %s)' % default_run_id)
    parser.add_argument('-t', '--time', action="store_true", dest="timing_run", default=False, 
                        help='record timing only (no memory stats) (default: %s)' % False)
    parser.add_argument('-a', '--algorithms', action="append", metavar="alg", dest="algorithms", default=[], nargs='+', 
                        help="the list of algorithms to use (default: all)")
    parser.add_argument('-n', '--dry-run', action='store_true', dest='dry_run', default=False, 
                        help='simulate the run only (no computation started)')
    parser.add_argument('-p', '--problem-range', type=str, metavar='R', dest='problem_range', default=':',
                        help='calculate only problems in the specified (Python) range, e.g. 1:10, 1::20 (default: all (:))')
    parser.add_argument('-m', '--max_card', type=str, metavar='C', dest='cardinalities', default='default',
                        help='calculate using max_card = C (e.g. 1 or 1,2 or 1,2,3)')
    args = parser.parse_args()

    Problem.read()
    if not os.path.exists(args.run_id):
        os.mkdir(args.run_id)
    os.chdir(args.run_id)

    if args.algorithms == [] or args.algorithms == [['all']]:
        algorithms  = ['hsdag-cache-picosat', 'hsdag-ci-cache-picosat']
    else:
        algorithms = [a for l in args.algorithms for a in l]   

    if args.recompute and not args.dry_run:
        remove_results_with_warning(args.run_id, algorithms, args.dry_run)
    
    problems    = eval('Problem.objects['+args.problem_range+']')
    samples     = irange(args.samples)
    if args.cardinalities != 'default':
        cards   = eval('[' + args.cardinalities + ']')
    else:
        cards   = [1]
    tasks       = (Task(algorithm=a, pid=p.pid, sample=s, card=c) for c in cards for p in problems for a in algorithms for s in samples)
    resume_task = Task(**get_status())
    filters     = set()
    inputfile   = Datafile('../inputs.txt')

    
    resumed = False
    last_task = Task(algorithm=None,pid=0,sample=0)
    last_problem = None
    inputline = None
    input = None
    stop_dueto_time = False
    stop_dueto_mem  = False
    
    resumed_tasks  = dropwhile(lambda task: task != resume_task, tasks) if not args.recompute else tasks
    filtered_tasks = ifilter(lambda task: all(map(lambda f: f(task), filters)), resumed_tasks)

    print formatted_values(("%27s", "Time"), ("%20s", "Experiment"), 
                ("%12s", "run"), ("%5s", "PID"), ("%7s", "MaxCard"), ("%25s", "Algorithm"), ("%12s","TotalTime"), 
                ("%5s", "#Diag"), ("%7s", "RSS"), ("%7s", "RSS/SAT"))

    for task in filtered_tasks:
        save_status(task)
        
        if not args.dry_run:
            gc.collect()
            
        problem = Problem.get(task.pid)
        if last_task.pid > 0:
            last_problem = Problem.get(last_task.pid)
        
    
        if (stop_dueto_time == True or stop_dueto_mem == True) and last_problem and problem.specsize != last_problem.specsize:
            algorithm = task.algorithm # important! copy the string here, or the closure will do wrong things
            filters.add(lambda t: t.algorithm != algorithm)
            print "Skipping algorithm %s due to limit (%f sec, %d MB)" % (task.algorithm, exectime, max_rss)
            stop_dueto_time = False
            stop_dueto_mem = False
            continue
    
        if args.dry_run:
            stats = {}
            max_rss = 0
            num_rss_polls = 0
            stop_dueto_time = False
            stop_dueto_mem = False
            start = datetime.now()
            print "%27s %20s %11s %5d %5d %20s" % (start, experiment, args.run_id, problem.pid, problem.specsize, task.algorithm)
            continue
        
        if task.pid != last_task.pid:
            inputline = inputfile.getline(task.pid)
            actual_pid, spec, int_diag, trace = inputline.split("\t")
            int_diag = parse(int_diag)
            spec_parsed = parse(spec)
            actual_pid = int(actual_pid)
            if actual_pid != task.pid:
                raise Exception("Something's wrong in the input file, expected PID %d on line %d, but got %d" % (task.pid, task.pid, actual_pid))
        
        if last_problem and problem.specsize != last_problem.specsize:
            stop_dueto_time = True
            stop_dueto_mem  = True
        
        tries = 0
        done = False
        while tries < 3 and not done:
            tries += 1
            try:
                with timeout_monitor(int(timeout_seconds * 2), True):
                    
                    start = datetime.now()
                    print formatted_values(("%27s", start), ("%20s", experiment), 
                        ("%12s", args.run_id), ("%5s", problem.pid), ("%7s", str(task.card)), 
                        ("%25s", task.algorithm)),
                    
                    sys.stdout.flush()
                    
                    # start up the python process with the algorithm and parameters
                    python_cmd = [PYTHONPATH, os.path.join(THIS_FILE_DIR, '../../pymbd/benchmark/ltl/compute_sample.py'), task.algorithm, str(task.card), str(timeout_seconds), "weak"]
                    python_process = Popen(python_cmd, stdout=PIPE, stdin=PIPE, stderr=STDOUT, close_fds=True)

                    memstat_runner = os.path.join(THIS_FILE_DIR, '../../pymbd/benchmark/memstat_new.py')
                
                    sat_solver_name = [s for r,s in SOLVER_BACKENDS.iteritems() if re.match(r, task.algorithm)][0]

                    memstat_cmd = [PYTHONPATH, memstat_runner]
                    memstat_process = Popen(memstat_cmd, stdout=PIPE, stdin=PIPE, stderr=STDOUT, close_fds=True)
    
                    memstat_process.stdin.write(str(python_process.pid) + " " + sat_solver_name)
                    memstat_process.stdin.close()
                    
                    
                    approx_begin = time.time()
                    output = python_process.communicate("\n".join([spec,trace]))[0].split("\n")
                    
                    if len(output) >= 2:
                        output_line = output[0]
                        stats = eval(output[1])
                        exectime = stats['total_time']
                        diff = diff_formulas(spec_parsed, int_diag)
                        diff = set(map(str, diff))
                        diagnoses = [] 
                        for line in output_line.split(",\t")[:-1]:
                            fff, t = line.split(" : ")
                            diagnoses.append((set(eval(fff)), float(t)))
                        found = False
                        for d,t in diagnoses:
                            if diff == d:
                                found = True
                        if diagnoses:
                            first_timestamp = min(map(lambda x: x[1], diagnoses))
                        else:
                            first_timestamp = -1
                        # print "intended diagnosis:", diff
                        # print "found diagnoses:", diagnoses
                        # print "found?", found
                    else:
                        output_line = "Invalid Output:" + " ".join(output).translate(None, "\n")
                        stats = dict()
                        exectime = time.time() - approx_begin
                        found = False
                        first_timestamp = -1
                    
                    # terminate the memory logger and get maximum rsize
                    os.kill(memstat_process.pid, signal.SIGTERM)
                    os.waitpid(memstat_process.pid, 0)
                    memstat_output = memstat_process.stdout.readlines()
                    # print memstat_output
                    try:
                        result = eval(memstat_output[0])
                    except:
                        print memstat_output
                        raise

                    num_hs = stats.get('num_hs',0)
                    max_rss = result[0] / 1024.0     # MiB
                    num_rss_polls = result[1]
                    timeout = result[2]
                    memout = result[3]
                    tp_max_rss = result[4].get(sat_solver_name,0) / 1024.0
                    
                    if timeout:
                        stats['timeout'] = True
                    p, t, s = problem, task, stats
                    Result.append(experiment=experiment, run_id=args.run_id, datetime=start, pid=t.pid, algorithm=t.algorithm, 
                                  specsize=p.specsize, specnumvars=p.specnumvars,tracesize=p.tracesize, tracestemsize=p.tracestemsize,
                                  found=found, first_timestamp=first_timestamp, memout=memout, max_rss=max_rss, 
                                  sat_max_rss=tp_max_rss, num_rss_polls=num_rss_polls, num_faults=problem.num_faults, max_card=t.card, 
                                  cache_hits_fm=0,
                                  **stats)
                    Datafile("output-%s.txt" % task.algorithm, mode="append").appendline("%s\t%d\t%s" % (start,t.pid,output_line))
            
                    if exectime < timeout_seconds:
                        stop_dueto_time = False
                    if max_rss < 2048:
                        stop_dueto_mem  = False
    
                    print formatted_values(("%12.6f",stats.get('total_time',exectime)), 
                        ("%5d", num_hs), ("%7.2f", max_rss), ("%7.2f", tp_max_rss))

                    sys.stdout.flush()
            
                    done = True
            
                # end with timeout
                    
            except Timeout:
                print "Timed out... trying again"
                        
            except KeyboardInterrupt:
                return 
        
            except:    
                algorithm = task.algorithm # important! copy the string here, or the closure will do wrong things
                filters.add(lambda t: t.algorithm != algorithm)
                print "Skipping algorithm %s due to exception" % task.algorithm
                print traceback.print_exc()
                print output
                sys.exit()
        
        last_task = task

    #end for
    save_status()

compute()

#from common.profile import profile, line_profile
#profile('compute()')
#line_profile('compute()', compute)

