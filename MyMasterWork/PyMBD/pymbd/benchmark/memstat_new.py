#!/usr/bin/env python
# sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'src'))
# sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'benchmark'))
from collections import defaultdict
import subprocess
import re
import mmap
import os
import signal
import sys
import time

begin = time.time()

rss_max = 0
count = 0
begin = time.time()
timeout = False
memout = False
children = []
children_rss_max = defaultdict(int)
total_rss = rss_max

def terminate(signum, frame):
    print str((rss_max, count, timeout, memout, dict(children_rss_max)))  
    print
    sys.stdout.flush()
    sys.exit()
 
signal.signal(signal.SIGHUP,  terminate)
signal.signal(signal.SIGINT,  terminate)
signal.signal(signal.SIGALRM, terminate)
signal.signal(signal.SIGTERM, terminate)

def get_rsize(pid):
    """
    returns the resident set size of a process with PID `pid` in kiB (kilobytes).
    uses the ps utility and distinguishes between Mac OS X and Linux platforms.
    """
    try:
        if sys.platform == "darwin":
            out = subprocess.check_output('/bin/ps -o rss= %d' % pid, shell=True)
            return int(out.strip())
        elif sys.platform.startswith('linux'):
            out = subprocess.check_output('ps -ly %d' % pid, shell=True)
            line = out.split("\n")[1]
            return int(line.split()[7])
    except subprocess.CalledProcessError:
#        import traceback
#        traceback.print_exc()
        return 0
    
def get_rsize2(cmd):
    """
    returns the resident set size of a given command name in kiB (kilobytes).
    uses the ps utility and distinguishes between Mac OS X and Linux platforms.
    """
    try:
        if sys.platform == "darwin":
            out = subprocess.check_output('/bin/ps -c -o rss=,command= | grep %s | grep -v grep' % cmd, shell=True)
            return sum(map(int, [x.strip().split()[0] for x in out.split("\n") if x]))
        elif sys.platform.startswith('linux'):
            out = subprocess.check_output('ps -ly ax | grep %s | grep -v grep' % cmd, shell=True)
            lines = out.split("\n")
            return sum(map(int, [x.strip().split()[7] for x in lines if x]))
    except subprocess.CalledProcessError:
        return 0

pid, childprocess = sys.stdin.read().split()
pid = int(pid)
rss_max = get_rsize(pid)

# PICOSAT_PIDFILE = os.path.dirname(os.path.abspath(__file__)) + '/../../../../../../hitting_set/trunk/lib/picosat/pid'
# while not os.path.exists(PICOSAT_PIDFILE):
    # time.sleep(0.05)
    
# file = open(PICOSAT_PIDFILE, "r+")
# size = os.path.getsize(PICOSAT_PIDFILE)
# pidfile = mmap.mmap(file.fileno(), size)
while 1:
    count += 1
    total_rss = rss_new = get_rsize(pid)

    if rss_new > rss_max:
        rss_max = rss_new
    
#    rss_new_picosat = get_rsize2(childprocess)
    picosatpid = None
    while picosatpid is None:
        # try:
            # pidfile.seek(0)
            # picosatpid = int(pidfile.readline().strip())
        # except ValueError:
            # picosatpid = None
            
    # if picosatpid != 0:
        # rss_new_picosat = get_rsize(picosatpid)
        # pidfile.seek(0)
        rss_new_picosat = get_rsize2(childprocess)

        if rss_new_picosat > children_rss_max.get(childprocess,0):
            children_rss_max[childprocess] = rss_new_picosat
    
    # kill watched process if rss > 2500MB or time > 600s
        if rss_max > 2300*1024:
            # print "killing worker process due to memory limit"
            os.kill(pid, signal.SIGKILL)
            memout = True
            
        #elif (time.time()-begin) > 600:
#            # print "killing worker process due to time limit"
#            os.kill(pid, signal.SIGKILL)
#            timeout = True
        
        if memout or timeout:
            print str((rss_max,count,timeout,memout, dict(children_rss_max)))
            sys.stdout.flush()
            sys.exit()
        
    if count > 1000:
        time.sleep(0.1)

sys.stdout.flush()

