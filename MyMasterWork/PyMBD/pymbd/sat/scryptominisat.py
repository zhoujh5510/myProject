from clause import Clause
from engine import ENGINES, Engine
from literal import Literal
from oddevenmergesort import CardinalityNetwork
from subprocess import PIPE
from ..util.two_way_dict import TwoWayDict
import math
import mmap
import os
import subprocess
import time

merge = lambda opts1, opts2: dict(opts1.items() + opts2.items())

ENGINES['scryptominisat']           = lambda o: SCryptoMinisatEngine(merge({'async':False}, o))
ENGINES['scryptominisat-async']     = lambda o: SCryptoMinisatEngine(merge({'async':True}, o))
ENGINES['scryptominisat-async-mod'] = lambda o: SCryptoMinisatEngine(merge({'async':True, 'cms-mod-variant':True}, o))

ENGINES['simple-scryptominisat']            = lambda o: SCryptoMinisatSimpleEngine(merge({'async':False}, o))
ENGINES['simple-scryptominisat-async']      = lambda o: SCryptoMinisatSimpleEngine(merge({'async':True}, o))
ENGINES['simple-scryptominisat-async-mod']  = lambda o: SCryptoMinisatSimpleEngine(merge({'async':True, 'cms-mod-variant':True}, o))


def to_dimacs_literal(literal, variable_map):
    if literal.sign == True:
        return str(variable_map.get_key(literal.name)+1)
    else:
        return "-" + str(variable_map.get_key(literal.name)+1)

def to_dimacs_clause(clause, variable_map):
    literals = map(lambda l: to_dimacs_literal(l, variable_map), clause.literals)
    return " ".join(literals) + " 0"


SCRYPTOMINISAT_PATH        = os.path.dirname(os.path.abspath(__file__)) + '/../../lib/SCryptoMinisat/SCryptoMinisat'
SCRYPTOMINISAT_EXECUTABLE  = SCRYPTOMINISAT_PATH + '/SCryptoMinisat'
SCRYPTOMINISAT_PIDFILE     = SCRYPTOMINISAT_PATH + '/pid'

if not os.path.exists(SCRYPTOMINISAT_PIDFILE):
    with open(SCRYPTOMINISAT_PIDFILE, "w") as f:
        f.write("0\n" + "0"*100+"\n")
        
file = open(SCRYPTOMINISAT_PIDFILE, "r+")
size = os.path.getsize(SCRYPTOMINISAT_PIDFILE)
pidfile = mmap.mmap(file.fileno(), size)

class SCryptoMinisatWrapper():
    
    def __init__(self):
        self.cnf = None
        self.outlines = None
        self.result = None
        self.get_valuation = False
        self.calculate_unsat_core = False
        self.solver_time = 0
        pidfile.seek(0)
        pidfile.write("0\n")
    
    def start(self, header, cnf=[], calculate_unsat_core=False, get_valuation=False, multiple_solutions_warning=True, logfile=None, time_map=None, start_time=None):

        self.cnf = cnf
#        print cnf
        self.calculate_unsat_core = calculate_unsat_core
        self.get_valuation = get_valuation
        
#        if os.path.exists(self.get_input_file_name()):
#            os.remove(self.get_input_file_name())
#        if os.path.exists(self.get_output_file_name()):
#            os.remove(self.get_output_file_name())
#        
#        with open(self.get_input_file_name(), "w") as f:
#            f.write(header)
#            for clauses in cnf:
#                f.write(clauses)
                
#        time.sleep(0.05)
        t0 = time.time()
#        p = subprocess.Popen([SCRYPTOMINISAT_EXECUTABLE] +  [self.get_input_file_name(), self.get_output_file_name()], stdout=PIPE)
        p = subprocess.Popen([SCRYPTOMINISAT_EXECUTABLE], stdin=PIPE, stdout=PIPE)
        
        pidfile.seek(0)
        pidfile.write(str(p.pid) + "\n")
#        print p.pid
#        time.sleep(10)
        out, unused_err = p.communicate(header + " " + " ".join(cnf))
        
        pidfile.seek(0)
        pidfile.write("0\n")
        t1 = time.time()
        self.solver_time = t1-t0
#        print self.solver_time
#        time.sleep(0.05)
#        with open(self.get_output_file_name(), "r") as f:
#            self.outlines = f.read().strip().split("\n")
        self.outlines = out.strip().split("\n")
        if len(self.outlines) > 3 and multiple_solutions_warning:
            print "*"*80
            print "*"*80
            print "** SCRYPTOMINISAT WARNING: this CNF has no unique solution. check your input! **"
            print "*"*80
            print "*"*80
#                raise Exception("")
            
    def parse_output(self, output_lines, get_valuation=False, calculate_unsat_core=False):
        if output_lines[0].strip() == 'SAT':
            output_values = []
            if get_valuation:
                # get values from remaining lines
                # be aware that only the last line is 0-terminated!
                for l in output_lines[1:2]:
#                for l in output_lines[3:4]:
                    for v in l.split(" "):
                        if v == "0":
                            break
                        output_values.append(int(v))
            return (True, output_values)
        elif output_lines[0].strip() == 'UNSAT':
            core = []
            return (False, core)
        else:
            raise RuntimeError("scryptominisat returned unexpected output: " + "\n".join(output_lines))
    
    def get_input_file_name(self):
        return SCRYPTOMINISAT_PATH + '/scryptominisat.in'
    
    def get_output_file_name(self):
        return SCRYPTOMINISAT_PATH + '/scryptominisat.out'
 
## ================================================================================================================= ##   

class SCryptoMinisatAsyncWrapper(SCryptoMinisatWrapper):
    
    def start(self, header, cnf=[], calculate_unsat_core=False, get_valuation=False, multiple_solutions_warning=True, logfile=None, time_map=None, start_time=None):
        self.cnf = cnf
        self.calculate_unsat_core = calculate_unsat_core
        self.get_valuation = get_valuation
#        
#        with open(self.get_input_file_name(), "w") as f:
#            f.write(header)
#            for clauses in cnf:
#                f.write(clauses) 
        
        out = []
        p = subprocess.Popen([SCRYPTOMINISAT_EXECUTABLE], stdout=PIPE, stdin=PIPE, close_fds=True)
        pidfile.seek(0)
        pidfile.write(str(p.pid) + "\n")

        t0 = time.time()
        
        p.stdin.write(header + " " + " ".join(cnf))
        p.stdin.close()
        
        i = 0
        for line in p.stdout:
            i += 1
#            line = p.stdout.readline().strip()
            out.append(line)
            if i % 2 == 0:
                _, diag = self.parse_output(out[-2:], get_valuation=True)
                if diag:
#                    print diag
                    if time_map is not None:
                        time_map[frozenset(diag)] = time.time() - start_time
                        logfile.write("%12.3f: found diagnosis of size %5d: %s\n" % (float(time.time() - start_time), len(diag), diag))
                        logfile.flush()

        pidfile.seek(0)
        pidfile.write("0\n")
        t1 = time.time()
        self.solver_time = t1-t0
        self.outlines = out 

## ================================================================================================================= ##
    
SENTENCE_INTERPRETERS = { }
VARIABLE_INTERPRETERS = { }    

class SCryptoMinisatEngine(Engine):
    
    """
    This is a high-level PicoSAT wrapper intended for the problem/description/engine/result mechanism in this 
    ``sat'' package. As such, it requires a description containing sentences and variables which will then 
    be converted to a CNF using the corresponding (registered) interpreters. For example, the ISCAS benchmark 
    framework contains sentences and interpreters for Boolean gates. 
    
    If the CNF has been constructed, it calls the low-level PicoSAT wrapper above. 
    """
    
    def __init__(self, options):
        super(SCryptoMinisatEngine, self).__init__(options)
        self.sentence_interpreters.update(SENTENCE_INTERPRETERS)
        self.variable_interpreters.update(VARIABLE_INTERPRETERS)
        self.cnf = ""
        self.cnf_cn = ""
        self.vars = {}
        self.cn_k = 0
        self.stats = {}
        self.time_map = None # {}
        self.logfile = None # open('scryptominisat.log', 'w')
        if self.options.get('cms-mod-variant',False):
            # HACK follows!!!
            global SCRYPTOMINISAT_PATH, SCRYPTOMINISAT_EXECUTABLE
            SCRYPTOMINISAT_PATH = os.path.dirname(os.path.abspath(__file__)) + '/../../lib/SCryptoMinisat-mod/SCryptoMinisat'
            SCRYPTOMINISAT_EXECUTABLE  = SCRYPTOMINISAT_PATH + '/SCryptoMinisat'

    
    def start(self, description=None, **options):
        super(SCryptoMinisatEngine, self).start(description, **options)

        self.start_time = time.time()
        
        if not self.cnf:
            vars = sorted(self.description.get_variables(), key=lambda x: not x.name.startswith("AB"))
            self.vars = TwoWayDict(dict((i, v.name) for i,v in enumerate(vars)))
            self.ab_vars = [i for i,n in self.vars.iteritems() if n.startswith("AB")]

            # add clauses for the input/output variables which are constrained
            self.core_map = {}
            self.clauses = []
            for s in self.description.get_sentences():
                self.clauses.extend(self.sentence_interpreters[type(s)](self, s, self.vars))
            for v in self.description.get_variables():
                if v.value is not None:
                    self.clauses.append(Clause([Literal(v.name, v.value)])) 
            
            for c in self.clauses:
                self.cnf += "\n" + to_dimacs_clause(c, self.vars)
            
            self.stats['cnf_clauses'] = len(self.clauses)
            self.max_out = max(self.ab_vars) + 1
            
        return self.solve()

    def start_again(self, new_sentences, **options):
        super(SCryptoMinisatEngine, self).start_again(new_sentences, **options)
        clauses = []
        for s in new_sentences:
            clauses.extend(self.sentence_interpreters[type(s)](self, s, self.vars))
        for c in clauses:
            self.cnf += "\n" + to_dimacs_clause(c, self.vars)
        self.stats['cnf_clauses'] += len(clauses)
            
        return self.solve()

    def solve(self):
        self.construct_cardinality_network(**self.options)
        
        cnf  = "cnf\n" + self.cnf + self.cnf_cn
        cnf += "\n\n-%d 0\n" % self.cn.vars[self.options.get('max_card',1)] 
        cnf += "\nend"
#        print self.max_out
#        print self.options['max_card']
        cnf += "\noutput %d" % self.max_out
#        cnf += "\nlimitsols 1000"
        
        if self.options.get('find_all_sols', False):
            cnf += "\nallsols"
        else:
            cnf += "\nsolve"

        self.stats['num_rules'] = self.stats.get('cnf_clauses',0) + self.stats.get('net_clauses',0) + 1
        self.stats['num_vars']  = max(self.cn.vars)

        if self.options['async']:        
            out = []
            result = []
            p = subprocess.Popen([SCRYPTOMINISAT_EXECUTABLE], stdout=PIPE, stdin=PIPE, close_fds=True)
            pidfile.seek(0)
            pidfile.write(str(p.pid) + "\n")
    
            t0 = time.time()
#            print "SCMS started at  %.6f" % time.time()
            
            with open(SCRYPTOMINISAT_PATH + "/scryptominisat.in", 'w') as f:
                f.write(cnf)
            
            p.stdin.write(cnf)
            p.stdin.close()
            
            i = 0
            for line in p.stdout:
                i += 1
                out.append(line)
                if i % 2 == 0:
                    diag = self.parse_partial_output(out[-2:])
                    if diag:
                        result.append(frozenset(diag))
                        if self.time_map is not None:
                            self.time_map[frozenset(diag)] = time.time() - self.start_time
                        if self.logfile is not None:
                            self.logfile.write("%12.3f: found diagnosis of size %5d: %s\n" % (float(time.time() - self.start_time), len(diag), diag))
                            self.logfile.flush()
#                if line.strip() == "DONE" and self.logfile is not None:
#                    self.logfile.write("%12.3f: UNSAT\n" % float(time.time() - self.start_time))
#                    self.logfile.flush()

            pidfile.seek(0)
            pidfile.write("0\n")
#            print "SCMS finished at %.6f" % time.time()
            t1 = time.time()
            self.solver_time = t1-t0
            self.outlines = out 
        else:
            with open(SCRYPTOMINISAT_PATH + "/scryptominisat.in", 'w') as f:
                f.write(cnf)
                
            t0 = time.time()
            p = subprocess.Popen([SCRYPTOMINISAT_EXECUTABLE], stdin=PIPE, stdout=PIPE)            
            pidfile.seek(0)
            pidfile.write(str(p.pid) + "\n")
            out, unused_err = p.communicate(cnf)
            pidfile.seek(0)
            pidfile.write("0\n")
            t1 = time.time()
            self.solver_time = t1-t0
            self.outlines = out.strip().split("\n")
        
        if self.options.get('find_all_sols', False) and self.options.get('max_card', None) > 0:
            if self.options['async']:
                self.result = result
            else:
                self.result = self.parse_all_outputs(self.outlines)
        else:
            self.result = self.parse_output(self.outlines)
#        print self.result
        return self.result

    def construct_cardinality_network(self, **options):

        k = 2**int(math.ceil(math.log(options.get('max_card',1)+1,2)))
        n = k*int(math.ceil(float(len(self.ab_vars))/k))

        if self.cn_k != k:
            self.cn_k = k
            self.cnf_cn = "\n"
            ab_vars_padded = map(lambda x: x+1, self.ab_vars)    # +1 because the CNF vars start from 1 while we start from 0
            vars_padded = dict(self.vars) 
            for i in xrange(max(self.vars)+2, max(self.vars)+(n-len(self.ab_vars))+2):    # +1: same reaseon as above
                ab_vars_padded += [i]
                vars_padded[i] = 'temp'
                self.cnf_cn += "\n-%d 0" % i
                self.stats['net_clauses'] = self.stats.get('net_clauses',0) + 1
            
            self.cn = CardinalityNetwork(list(ab_vars_padded), next_var=max(vars_padded)+2)
            net_clauses = self.cn.card(range(len(ab_vars_padded)), k)
            self.cnf_cn += "\n"
            for c in net_clauses:
                self.cnf_cn += "\n" + " ".join(map(str, c+[0]))
            self.stats['net_clauses'] = self.stats.get('net_clauses',0) + len(net_clauses)

    def register_core_sentence(self, id, sentence):
        self.core_map[id] = sentence

    def parse_partial_output(self, output_lines):
        if output_lines[0].strip() == "SAT" and len(output_lines) > 1:
            output_values = []
            assignment = output_lines[-1]
            for v in assignment.split(" "):
                v = int(v)
                if v == 0:
                    break
                if v > 0:
                    output_values.append(self.map_back(v))
            return output_values
        else:
            return None
            
    def map_back(self, v):
        v = (v - 1) if v > 0 else (v + 1) # compensate the DIMACS offset
        return self.vars[abs(v)][3:]

    def parse_output(self, output_lines):
        if output_lines[0].strip() == "UNSAT":
            return None
        else:
            if output_lines[-1].strip() == "DONE" or output_lines[0].strip() == "SAT":
                output_values = []
                assignment = output_lines[-2]
                for v in assignment.split(" "):
                    v = int(v)
                    if v == 0:
                        break
                    if v > 0:
                        output_values.append(self.map_back(v))
                return output_values
            elif output_lines[0].strip() == "SAT":
                return None
            else:
                print "Something went wrong with SCryptoMiniSAT, did not print UNSAT and DONE at the end."
                return None

    def parse_all_outputs(self, output_lines):
        if output_lines[0].strip() == "UNSAT":
            return None
        else:
            if output_lines[-1].strip() == "DONE":
                output_values = []
                for assignment in output_lines[1:-1:2]:
                    output_assignment = []
                    for v in assignment.split(" "):
                        v = int(v)
                        if v == 0:
                            break
                        if v > 0:
                            output_assignment.append(self.map_back(v))
                    output_values.append(frozenset(output_assignment))
                return output_values
            elif output_lines[0].strip() == "SAT":
                return None
            else:
                print "Something went wrong with SCryptoMiniSAT, did not print UNSAT and DONE at the end."
                return None


class SCryptoMinisatSimpleEngine(SCryptoMinisatEngine):
    
    def __init__(self, options):
        super(SCryptoMinisatSimpleEngine, self).__init__(options)
        self.logfile = None # open('scryptominisat.log', 'w')
    
    def start(self, description=None, **options):
        self.options.update(options)
        self.ab_vars = options.get('ab_vars')
        self.options['num_vars'] = description.num_vars
        self.cnf = "\n\n".join(description.cnf)
        self.max_out = options.get('max_out', max(self.ab_vars))
        self.start_time = time.time()
        return self.solve()

    def start_again(self, description, **options):
        self.options.update(options)
        self.ab_vars = options.get('ab_vars')
        self.options['num_vars'] = description.num_vars
        self.cnf = "\n\n".join(description.cnf)
            
        return self.solve()

    def construct_cardinality_network(self, **options):

        k = 2**int(math.ceil(math.log(options.get('max_card',1)+1,2)))
        n = k*int(math.ceil(float(len(self.ab_vars))/k))

        if self.cn_k != k:
            self.cn_k = k
            self.cnf_cn = "\n"
            ab_vars_padded = map(lambda x: x, self.ab_vars)
            for i in xrange(options['num_vars']+1, options['num_vars']+(n-len(self.ab_vars))+1):    # +1: same reaseon as above
                ab_vars_padded += [i]
                self.cnf_cn += "\n-%d 0" % i
                options['num_vars'] += 1
           
            self.cn = CardinalityNetwork(list(ab_vars_padded), next_var=options['num_vars']+1)
#            print "CN input vars:", self.cn.vars
            self.clauses_cn = self.cn.card(range(len(ab_vars_padded)), k)
#            print "CN output vars:", self.cn.vars
            self.cnf_cn += "\n"
            for c in self.clauses_cn:
                self.cnf_cn += "\n" + " ".join(map(str, c+[0]))

    def map_back(self, v):
        return v

######## old: using the OddEvenMergeSortNetwork

# # the OEMS network must have a 2**n entries, so we need to pad with some auxiliary variables
# # and set them to 0 in the CNF
# size = len(ab_vars)
# size_new = 2**int(math.ceil(math.log(size,2)))
# 
# self.cnf += "\n\n"
# ab_vars_padded = map(lambda x: x+1, ab_vars)    # +1 because the CNF vars start from 1 while we start from 0 
# for i in xrange(max(ab_vars)+2, max(ab_vars)+(size_new-size)+2):    # +1: same reaseon as above
#     ab_vars_padded += [i]
#     self.cnf += "\n-%d 0" % i
# 
# self.cnf += "\n"
# oems = OddEvenMergeSortNetwork(list(ab_vars_padded))
# sorter_clauses = oems.oddevenmergesort(range(len(ab_vars_padded)))
# for c in sorter_clauses:
#     self.cnf += "\n" + " ".join(map(str, c+[0]))
# self.cnf += "\n\n"
#     
# self.cnf += "\nend"
# self.cnf += "\nminimize unary " + " ".join(map(str, oems.vars + [0]))

######## /old: using the OddEvenMergeSortNetwork