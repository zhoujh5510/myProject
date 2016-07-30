#!/usr/bin/env python
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from subprocess import Popen, PIPE, STDOUT
from datetime import datetime
from pymbd.benchmark.csv_framework import *
from pymbd.util.irange import irange
from data_structures import *
import traceback
import argparse
import signal
import time
import gc
import re

PYTHONPATH = 'python'
THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.setrecursionlimit(2**16)
SOLVER_BACKENDS = {r".*yices.*":"yices", r".*picosat.*":"picosat", r".*scrypto.*":"SCryptoMinisat", r".*":"xxx"}


def compute():
    experiment          = "experiment03"
    default_run_id      = "run01"
    default_sample_size = 1
    
    parser = argparse.ArgumentParser(description='Compute problems')
    modes = parser.add_mutually_exclusive_group()
    parser.add_argument('-i', '--input-file', type=str, metavar="FILE", default="inputs.txt", dest="inputfile", 
                       help="the input file used for computation")
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
    parser.add_argument('-m', '--max-card', type=str, metavar='PYLIST', default='3', dest='cards',
                        help="a list of max-cardinalities for which to calculate the diagnoses")
    args = parser.parse_args()
    
    input_file = os.path.abspath(args.inputfile)
    
    Problem.read()
    if not os.path.exists(args.run_id):
        os.mkdir(args.run_id)
    os.chdir(args.run_id)
    
    if args.algorithms == [] or args.algorithms == [['all']]:
        algorithms  = ['hsdag', 'hst', 'bool-it-h5-stop', 'bool-rec-h1-oldr4', 'saths', 'maxsaths']
    else:
        algorithms = [a for l in args.algorithms for a in l]
    
    if args.recompute:
        remove_results_with_warning(args.run_id, algorithms)


    problems    = eval('Problem.objects['+args.problem_range+']')
    samples     = irange(args.samples)
    cards       = eval('['+args.cards+']')
    tasks       = (Task(card=c, algorithm=a, pid=p.pid, sample=s)   
                   for p in problems for s in samples for a in algorithms for c in cards)
    resume_task = Task(**get_status())
    filters     = set()
    inputfile   = Datafile(input_file)
    
    resumed = False
    last_task = Task(card=0,algorithm=None,pid=0,sample=0)
    inputline = None
    input = None
    
    print formatted_values(("%27s", "Time"), ("%20s", "Experiment"), 
        ("%12s", "run"), ("%5s", "PID"), ("%7s", "MaxCard"), ("%25s", "Algorithm"), ("%12s","TotalTime"), 
        ("%5s", "#Diag"), ("%7s", "RSS"), ("%7s", "RSS/SAT"))

    for task in tasks:
        if (not resumed) and (task == resume_task) and (not args.recompute):
            resumed = True
        if ((resumed or args.recompute) and all(map(lambda f: f(task), filters))):        
            save_status(task)
            
            try:
            
                if not args.dry_run:
                    gc.collect()
                problem = Problem.get(task.pid)
                
                start = datetime.now()

                print formatted_values(("%27s", start), ("%20s", experiment), 
                    ("%12s", args.run_id), ("%5s", problem.pid), ("%7s", str(task.card)), 
                    ("%25s", task.algorithm)),

                sys.stdout.flush()

                if args.dry_run:
                    stats = {}
                    exectime = 0
                    max_rss = 0
                    num_hs = 0
                    num_rss_polls = 0
                    stop_dueto_time = False
                    stop_dueto_mem = False
                else:            
            
                    if task.pid != last_task.pid:
                        inputline = inputfile.getline(task.pid)

                    max_card = task.card if task.card else sys.maxint
    
                    prune = True
                    max_time = 330
                    
                    python_cmd = [PYTHONPATH, os.path.join(THIS_FILE_DIR, '../../pymbd/benchmark/mhs/compute_sample.py'), task.algorithm, str(max_card), str(prune), str(max_time)]
                    python_process = Popen(python_cmd, stdout=PIPE, stdin=PIPE, stderr=STDOUT, close_fds=True)
    
                    memstat_runner = os.path.join(THIS_FILE_DIR, '../../pymbd/benchmark/memstat_new.py')
                
                    sat_solver_name = [s for r,s in SOLVER_BACKENDS.iteritems() if re.match(r, task.algorithm)][0]
                    
                    memstat_cmd = [PYTHONPATH, memstat_runner]
                    memstat_process = Popen(memstat_cmd, stdout=PIPE, stdin=PIPE, stderr=STDOUT, close_fds=True)
    
                    memstat_process.stdin.write(str(python_process.pid) + " " + sat_solver_name)
                    memstat_process.stdin.close()
    
                    approx_begin = time.time()
                    output = python_process.communicate(inputline + "\n")[0].split("\n")

                    if len(output) >= 2:
                        output_line = output[0] 
                        if not re.match('^[0-9|,]*$', output_line):
                            print str.join("\n",output)
                            output_line = "Invalid Output:" + " ".join(output).translate(None, "\n")
                            stats = dict()
                            exectime = time.time() - approx_begin
                        else:
                            stats = eval(output[1])
                            exectime = stats.get('total_time',0) - stats.get('tp_time_check',0) - stats.get('tp_time_comp', 0)
                    else:
                        output_line = "Invalid Output:" + " ".join(output).translate(None, "\n")
                        stats = dict()
                        exectime = time.time() - approx_begin
                    
                    num_hs = stats.get('num_hs',0)
                    
                    # terminate the memory logger and get maximum rsize
                    # terminate the memory logger and get maximum rsize
                    os.kill(memstat_process.pid, signal.SIGTERM)
                    os.waitpid(memstat_process.pid, 0)
                    memstat_output = memstat_process.stdout.readlines()
                    try:
                        result = eval(memstat_output[0])
                    except:
                        print memstat_output
                        raise
                    
                    max_rss = result[0] / 1024.0     # MiB
                    num_rss_polls = result[1]
                    timeout = result[2]
                    memout = result[3]
                    tp_max_rss = result[4].get(sat_solver_name,0) / 1024.0
                                     
                    Result.append(experiment=experiment, run_id=args.run_id, datetime=start, pid=task.pid, exectime=exectime, 
                                  algorithm=task.algorithm, max_card=task.card if task.card else 0, 
                                  ncomp=problem.ncomp, tp_time_check=stats.get('tp_time_check',0), 
                                  tp_time_comp=stats.get('tp_time_comp',0), nnodes=stats.get('num_nodes', 0), ngen_nodes=stats.get('num_gen_nodes', 0), 
                                  ntp_check_calls=stats.get('num_tpcalls_check',0), ntp_comp_calls=stats.get('num_tpcalls_comp',0), nmhs=num_hs, 
                                  max_rss=max_rss, nrss_polls=num_rss_polls,
                                  timeout=timeout,memout=memout,nh_calls=stats.get('num_h_calls', 0),file=problem.file, tp_max_rss=tp_max_rss,
                                  cache_hits=stats.get('cache_hits',0), cache_misses=stats.get('cache_misses',0), cache_size=stats.get('cache_size',0),
                                  ncs=stats.get('num_cs',0), neffcs=stats.get('num_min_cs',0), mhshash="")
                    Datafile("output-%s.txt" % task.algorithm, mode="append").appendline("%s\t%d\t%s" % (start,task.pid,output_line))
        
                print formatted_values(("%12.6f",stats.get('total_time',exectime)), 
                    ("%5d", num_hs), ("%7.2f", max_rss), ("%7.2f", tp_max_rss))
                
                sys.stdout.flush()
                
                # if exectime > 300 or max_rss > 2048:
                    # algorithm = task.algorithm # important! copy the string here, or the closure will do wrong things
                    # filters.add(lambda t: t.algorithm != algorithm)
                    # print "Skipping algorithm %s due to limit (%f sec, %d MB)" % (task.algorithm, exectime, max_rss)
                    
            except KeyboardInterrupt:
                os.kill(python_process.pid, signal.SIGKILL)
                return 
            
            except:    
                # algorithm = task.algorithm # important! copy the string here, or the closure will do wrong things
                # filters.add(lambda t: t.algorithm != algorithm)
                # print "Skipping algorithm %s due to exception" % task.algorithm
                print traceback.print_exc()
            
            last_task = task

    #end for
    save_status()

compute()


