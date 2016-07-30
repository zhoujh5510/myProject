from itertools import dropwhile
from clause import Clause
from description import SimpleDescription, ClauseSentence, WeightSentence, \
    BlockingClauseSentence
from engine import Engine, ENGINES
from literal import Literal
from oddevenmergesort import CardinalityNetwork
from result import Result
from variable import Variable
from subprocess import Popen, PIPE, STDOUT
from ..util.two_way_dict import TwoWayDict
import math
import mmap
import os
import subprocess
import threading
import time

merge = lambda opts1, opts2: dict(opts1.items() + opts2.items())

ENGINES['yices'] = lambda o: YicesEngine(o)
ENGINES['yices-maxsat'] = lambda o: YicesMaxSatEngine(o)
ENGINES['yices-maxsat-cnf'] = lambda o: YicesMaxSatEngine(merge({'use_cnf':True}, o))
ENGINES['yices-maxsat-dimacs'] = lambda o: YicesDimacsEngine(merge({}, o))
ENGINES['yices-cn-dimacs'] = lambda o: YicesCnEngine(merge({}, o))
ENGINES['yices-cn-cnf'] = lambda o: YicesCnCnfEngine(merge({}, o))


ENGINES['simple-yices-maxsat'] = lambda o: SimpleYicesWrapper(o)
ENGINES['simple-yices-cn-dimacs'] = lambda o: SimpleYicesCnWrapper(o)

YICES_EXECUTABLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib', 'yices')

"""
contains a mapping from a Sentence type to a converter returning code specific 
to the engine
"""
SENTENCE_INTERPRETERS = { }

"""
contains a mapping from Variable type to a converter returning code specific 
to the engine
"""
VARIABLE_INTERPRETERS = { }

SENTENCE_INTERPRETERS_CNF = {}
VARIABLE_INTERPRETERS_CNF = {}


def parse_yices_output(output):
    values = {}
    for r in output:
        l = r.split()
        name = l[1]
        value = l[2][:-1]
        values[name] = True if value == "true" else (False if value == "false" else value)
    return values

## ================================================================================================================= ##

class YicesEngine(Engine):
    
    """
    High-level yices wrapper similar to the MiniSAT and PicoSAT wrappers (i.e. sentences, variables, ...)
    
    To use this, you need to make sure that the "yices" binary is available in your path! 
    Tested with yices 1.0.29 (this will probably not work with yices 2 as it has a different syntax I think). 
    """
    
    yices_in = []
    yices_out = []
    
    def __init__(self, options = {}):
        super(YicesEngine, self).__init__(options)
        if options.get('use_cnf',False) == True:
            self.sentence_interpreters.update(SENTENCE_INTERPRETERS_CNF)
            self.variable_interpreters.update(VARIABLE_INTERPRETERS_CNF)
        else:
            self.sentence_interpreters.update(SENTENCE_INTERPRETERS)
            self.variable_interpreters.update(VARIABLE_INTERPRETERS)
        self.num_queries = 0
        self.process = Popen(YICES_EXECUTABLE_PATH, stdout=PIPE, stdin=PIPE, stderr=STDOUT, close_fds=True)
        self.reset_core_sentences()
        self.times = []
        self.options['check_cmd'] = options.get('check_cmd', 'check')
        self.options['clear_core_sentences'] = options.get('clear_core_sentences', True)
        self.is_finished = False

    def start(self, description, **options):
        super(YicesEngine, self).start(description, **options)
        self.reset_core_sentences()
        cmd = self.create_yices_code()
        output_lines = self.yices_query(cmd)
#        YicesEngine.yices_in = []
#        YicesEngine.yices_out = []
#        print "\n".join(YicesEngine.yices_out)
        
        self.result = self.create_result(output_lines)
    
    def start_again(self, new_sentences, **options):
        super(YicesEngine, self).start_again(new_sentences, **options)
        if self.options['clear_core_sentences']:
            self.ids = {} # clear old core sentences, but do not reset counter!
        code = []
        for s in new_sentences:
            code.append(self.sentence_interpreters[type(s)](self, s, None))
        code.append("(%s)" % self.options['check_cmd'])
        cmd = "\n".join(code)
        output_lines = self.yices_query(cmd)
        self.result = self.create_result(output_lines)
        if self.options['clear_core_sentences']:
            self.ids = {}
    
    def yices_query(self, cmd):
        if self.is_finished:
            print "ERROR: calling yices_query on finished instance"
            return None
        
        cmd += "\n(echo \"@\\n\")\n"
        YicesEngine.yices_in.append(cmd)
        YicesEngine.yices_out.append("")
        
#        print cmd

        def _readerthread(fh, buffer):
            while 1:
                line = fh.readline().strip()
                if line == "@":
                    return
                if line.startswith("Error:"):
                    raise Exception("Yices " + line)
                buffer.append(line)

        content = []
        stdout_thread = threading.Thread(target=_readerthread, args=(self.process.stdout, content))
        stdout_thread.start()

        t0 = time.time()
        
        # write command to yices, the dot is added to recognise the end of the output
        self.process.stdin.write(cmd)
        
        stdout_thread.join()
            
        t1 = time.time()
        self.times.append(t1-t0)
        
#        print content
        
        lines = filter(lambda line: line and line != "s" and line != "searching..." and not line.startswith("Logical context"), content)
        
        if len(lines) == 0:
            print "Uh! Oh! There was a problem with the yices output!"
            print content
            return
        return lines
    
    def reset_core_sentences(self):
        self.last_id = 0
        self.ids = {}
    
    def register_core_sentence(self, unused_id, sentence):
        self.last_id += 1
        self.ids[self.last_id] = sentence
    
    def create_result(self, output_lines):
        ids = filter(lambda i: i.startswith("id: "), output_lines)
        [output_lines.remove(i) for i in ids]
        if 'ss' in output_lines:
            output_lines.remove('ss')
        if(output_lines[0] == 'sat'):
            output_values = parse_yices_output(output_lines[1:])
            return Result(True, output_values, [])
        elif(output_lines[0] == 'unsat'):
            # mapping the indices of the output 'unsat core ids: 2 4 6' to the
            # registered core sentences
            core = []
            if len(output_lines) > 1:
                core = map(lambda x: int(x), output_lines[1][16:].split(" "))
                core = map(lambda x: self.ids[x], core)
            return Result(False, {}, core)
        else:
            print "Uh oh! this one is neither SAT nor UNSAT?"
            print output_lines
    
    def finished(self):
        self.is_finished = True
        self.process.kill()
        self.process.wait()
        
    def create_yices_code(self):
        code = []
        code.append("(reset)")
        if self.options.get('calculate_unsat_core', True) != False:
            code.append("(set-verbosity! 2)")
            code.append("(set-evidence! true)")
        for v in self.description.get_variables():
            code.append(self.variable_interpreters[v.type](v))
        for s in self.description.get_sentences():
            code.append(self.sentence_interpreters[type(s)](self, s, None))
        code.append("(%s)" % self.options['check_cmd'])
        return "\n".join(code)


def bool_var(v):
    """
    >>> bool_var('n1', None)
    '(define n1::bool)'
    
    >>> bool_var('x23gat', False)
    '(define x23gat::bool false)'
    
    >>> bool_var('x23gat', True)
    '(define x23gat::bool true)'
    """
    return "(define %s::bool%s)" % (v.name, ("" if v.value is None else " " + str(v.value).lower()))

VARIABLE_INTERPRETERS[Variable.BOOLEAN] = bool_var
VARIABLE_INTERPRETERS_CNF[Variable.BOOLEAN] = bool_var

SENTENCE_INTERPRETERS_CN_CNF = {}
VARIABLE_INTERPRETERS_CN_CNF = {}
VARIABLE_INTERPRETERS_CN_CNF[Variable.BOOLEAN] = bool_var


class YicesCnCnfEngine(YicesEngine):
        
    def __init__(self, options = {}):
        super(YicesCnCnfEngine, self).__init__(options)
        self.sentence_interpreters = {}
        self.variable_interpreters = {}
        self.sentence_interpreters.update(SENTENCE_INTERPRETERS_CN_CNF)
        self.variable_interpreters.update(VARIABLE_INTERPRETERS_CN_CNF)
        self.cn_k = None
        self.stats = {}

    def create_yices_code(self):
        code = []
        
#        print self.options.get("ab_vars", [])
        
        code.append("(reset)")
        if self.options.get('calculate_unsat_core', True) != False:
            code.append("(set-verbosity! 2)")
            code.append("(set-evidence! true)")
        self.construct_cardinality_network(**self.options)
        for v in self.description.get_variables():
            code.append(self.variable_interpreters[v.type](v))
        for s in self.description.get_sentences():
            if type(s) in self.sentence_interpreters:
                code.append(self.sentence_interpreters[type(s)](self, s, None))
        code.append(self.code_cn)
        
        code.append("(assert (not %s))" % self.mapping[self.cn.vars[self.options.get('max_card',1)]])
        
        self.stats['num_vars'] = len(self.description.get_variables())
        self.stats['num_rules'] = len(self.description.get_sentences()) + self.code_cn.count("\n") + 1
        
        code.append("(%s)" % self.options['check_cmd'])
        return "\n".join(code)

    def create_result(self, output_lines):
        output_lines = list(dropwhile(lambda x: x not in ['sat', 'unsat'], output_lines))
        result = super(YicesCnCnfEngine, self).create_result(output_lines)
        if result:
            return [k[3:] for k,v in result.values.iteritems() if  k.startswith("AB") and v is True]

    def construct_cardinality_network(self, **options):

        self.mapping = dict(enumerate(self.options.get('ab_vars', []), 1))
        self.ab_vars = self.mapping.keys()
        k = 2**int(math.ceil(math.log(options.get('max_card',1)+1,2)))
        n = k*int(math.ceil(float(len(self.ab_vars))/k))

        if self.cn_k != k:
            self.cn_k = k
            self.cnf_cn = "\n"
            
#            print "constructing network for k=%d" % k
            
            ab_vars_padded = map(lambda x: x, self.ab_vars)
            
            for i in xrange(max(self.ab_vars)+1, max(self.ab_vars)+(n-len(self.ab_vars))+1):
                ab_vars_padded += [i]
                self.cnf_cn += "\n-%d 0" % i
                self.description.variables.append(Variable("cn_%d"%i, Variable.BOOLEAN, False))
                self.mapping[i] = "cn_%d"%i
                
#            print self.ab_vars
#            print ab_vars_padded
           
            self.cn = CardinalityNetwork(list(ab_vars_padded), next_var=max(ab_vars_padded)+1)
            self.clauses_cn = self.cn.card(range(len(ab_vars_padded)), k)
            
#            print self.clauses_cn
#            print self.cn.vars
            
            for i in range(max(ab_vars_padded)+1, max(self.cn.vars)+1):
                self.description.variables.append(Variable("cn_%d"%i, Variable.BOOLEAN, None))
                self.mapping[i] = "cn_%d"%i

            self.code_cn = ""
            for clause in self.clauses_cn:
                self.code_cn += "\n(assert (or " + " ".join([("(not " if l < 0 else "") + self.mapping[abs(l)] + (")" if l < 0 else "") for l in clause]) + "))"
            

def debug():
    with open('yices-debug.ys', 'w') as f:
        f.write("\n".join(YicesEngine.yices_in))
    with open("yices-debug.txt", 'w') as f:
        f.write("\n".join(YicesEngine.yices_out))
    

YICES_TMP_PATH    = os.path.dirname(os.path.abspath(__file__)) + '/../../lib/'
YICES_PIDFILE     = YICES_TMP_PATH + '/pid'

if not os.path.exists(YICES_PIDFILE):
    with open(YICES_PIDFILE, "w") as f:
        f.write("0\n" + "0"*100+"\n")
        
file = open(YICES_PIDFILE, "r+")
size = os.path.getsize(YICES_PIDFILE)
pidfile = mmap.mmap(file.fileno(), size)
    
SENTENCE_INTERPRETERS_DIMACS = {}
    
class YicesMaxSatEngine(YicesEngine):

    def __init__(self, options = {}):
        super(YicesMaxSatEngine, self).__init__(options)
        self.options['check_cmd'] = 'max-sat'
        self.options['clear_core_sentences'] = False

    def create_result(self, output_lines):
#        print output_lines
    
        ids = filter(lambda i: i.startswith("id: "), output_lines)
        [output_lines.remove(i) for i in ids]
        if 'ss' in output_lines:
            output_lines.remove('ss')
        
#        if not output_lines:
#            return None
        
        if 'cost' in output_lines[0]:
            output_lines = output_lines[1:]
        
        sat = output_lines[0] == "sat"
        if not sat:
            return None
        
        size = int(output_lines[-1].split(" ")[1])
        if size == 0:
            return None
        
        ids = map(int, output_lines[1][len("unsatisfied assertion ids: "):].split(" "))
        ids = map(lambda x: self.ids[x][1:], ids)
        if size != len(ids):
            print "Hm... yices said cost=%d but printed only %d ids..." % (size, len(ids))
        return ids

## ================================================================================================================= ##

class YicesDimacsEngine(Engine):
    
    def __init__(self, options = {}):
        super(YicesDimacsEngine, self).__init__(options)
        self.sentence_interpreters.update(SENTENCE_INTERPRETERS_DIMACS) 
        self.num_queries = 0
        self.times = []
        self.is_finished = False
        self.vars = {}
        self.next_var = 1
        self.MAX_WEIGHT = 1
        self.ab_vars = {}

    def start_again(self, new_sentences, **options):
        super(YicesDimacsEngine, self).start_again(new_sentences, **options)

        new_clauses = []
        for s in new_sentences:
            for c in self.sentence_interpreters[type(s)](self, s, None):
                new_clauses.append(self.to_dimacs_clause(c, self.vars))
        
        self.num_clauses += len(new_clauses)
        self.cnf += "\n" + "\n".join(new_clauses)
                
        cnf_input = "p wcnf %d %d\n" % (max(self.vars.values()), self.num_clauses) + self.cnf
        with open(self.get_input_file_name(), "w") as f:
            f.write(cnf_input)
                
        t0 = time.time()
        p = subprocess.Popen([YICES_EXECUTABLE_PATH, '-e', '-d', '-ms' ], stdin=PIPE, stdout=PIPE) # '-mw', str(self.MAX_WEIGHT)
        
        pidfile.seek(0)
        pidfile.write(str(p.pid) + "\n")
        out, unused_err = p.communicate(cnf_input)
        
        pidfile.seek(0)
        pidfile.write("0\n")
        t1 = time.time()
        self.solver_time = t1-t0
        self.outlines = out.strip().split("\n")
        self.whole_result = self.create_result(self.outlines)
        self.result = self.whole_result.values
        
            
    def start(self, description, **options):
        super(YicesDimacsEngine, self).start(description, **options)

        self.num_clauses, self.cnf = self.create_yices_code()
        
        cnf_input = "p wcnf %d %d\n" % (max(self.vars.values()), self.num_clauses) + self.cnf
        with open(self.get_input_file_name(), "w") as f:
            f.write(cnf_input)
                
        t0 = time.time()
        p = subprocess.Popen([YICES_EXECUTABLE_PATH, '-e', '-d', '-ms' ], stdin=PIPE, stdout=PIPE) # '-mw', str(self.MAX_WEIGHT)
        
        pidfile.seek(0)
        pidfile.write(str(p.pid) + "\n")
        out, unused_err = p.communicate(cnf_input)
        
        pidfile.seek(0)
        pidfile.write("0\n")
        t1 = time.time()
        self.solver_time = t1-t0
        self.outlines = out.strip().split("\n")
        self.whole_result = self.create_result(self.outlines)
        self.result = self.whole_result.values

    def create_yices_code(self):
        code = []
        for v in self.description.get_variables():
            self.vars[v.name] = self.next_var
            self.next_var += 1
            if v.value is not None:
                code.append(self.to_dimacs_clause(Clause([Literal(v.name, v.value)], weight=self.MAX_WEIGHT + 1), self.vars))
        for s in self.description.get_sentences():
            for c in self.sentence_interpreters[type(s)](self, s, None):
                code.append(self.to_dimacs_clause(c, self.vars))
        return len(code), "\n".join(code)

    def get_input_file_name(self):
        return YICES_TMP_PATH + '/yices.in'
    
    def to_dimacs_literal(self, literal, variable_map):
        if literal.sign == True:
            return str(variable_map.get(literal.name, 'XX'))
        else:
            return "-" + str(variable_map.get(literal.name, 'XX'))
    
    def to_dimacs_clause(self, clause, variable_map):
        literals = map(lambda l: self.to_dimacs_literal(l, variable_map), clause.literals)
        if clause.weight:
            return str(clause.weight) + " " + " ".join(literals) + " 0"
        else:
            return str(self.MAX_WEIGHT + 1) + " " + " ".join(literals) + " 0"
        
    def create_result(self, output_lines):
#        print self.ab_vars
        if(output_lines[0] == 'sat'):
            output_values = []
            assignment = output_lines[1]
            for v in assignment.split(" "):
                var_num = int(v.strip("-"))
#                print var_num
                if var_num == 0 :
                    break
                elif var_num in self.ab_vars and not v.startswith("-"):
                    output_values.append(self.ab_vars[var_num][3:])
            return Result(True, output_values, [])
        elif(output_lines[0] == 'unsat'):
            return Result(False, {}, [])
        else:
            print "Uh oh! this one is neither SAT nor UNSAT?"
            print output_lines
            
    def register_core_sentence(self, id, sentence):
        self.ab_vars[self.vars[id]] = id
            
## ================================================================================================================= ##

class SimpleYicesWrapper(object):
    
    def __init__(self, options={}):
        self.cnf = None
        self.outlines = None
        self.result = None
        self.get_valuation = False
        self.calculate_unsat_core = False
        self.solver_time = 0
        pidfile.seek(0)
        pidfile.write("0\n")
        self.options = options
    
    def start(self, sd, **options):

        self.options.update(options)
        
        self.cnf = cnf = sd.cnf
        
        if type(cnf) == list:
            cnf = "\n".join(cnf)
        
        if self.options.get('weighted',False):
            header = "p wcnf %d %d\n" % (sd.num_vars, sd.num_clauses)
            opts = ['-e', '-d', '-ms', '-mw', '2']
        else:
            header = "p cnf %d %d\n" % (sd.num_vars, sd.num_clauses)
            opts = ['-e', '-d']

        with open(self.get_input_file_name(), "w") as f:
            f.write(header + "\n" + cnf)
                
        t0 = time.time()
        p = subprocess.Popen([YICES_EXECUTABLE_PATH] + opts, stdin=PIPE, stdout=PIPE)
        
        pidfile.seek(0)
        pidfile.write(str(p.pid) + "\n")
        out, unused_err = p.communicate(header + "\n" + cnf)
        
        pidfile.seek(0)
        pidfile.write("0\n")
        t1 = time.time()
        self.solver_time = t1-t0
        self.outlines = out.strip().split("\n")
        self.result = self.parse_output(self.outlines)
        
    def start_again(self, sd, **options):
        return self.start(sd, **options)

    def parse_output(self, output_lines):
        if(output_lines[0] == 'sat'):
            output_values = []
            assignment = output_lines[1]
            for v in assignment.split(" "):
                var_num = int(v)
                if var_num == 0 :
                    break
                else:
                    output_values.append(var_num)
            return output_values
        elif(output_lines[0] == 'unsat'):
            return None
        else:
            print "Uh oh! this one is neither SAT nor UNSAT?"
            print output_lines

    def get_input_file_name(self):
        return YICES_TMP_PATH + '/yices.in'
            
    def get_result(self):
        return self.result
            
## ================================================================================================================= ##

class SimpleYicesCnWrapper(SimpleYicesWrapper):
    
    def __init__(self, options={}):
        self.cnf = None
        self.outlines = None
        self.result = None
        self.get_valuation = False
        self.calculate_unsat_core = False
        self.solver_time = 0
        pidfile.seek(0)
        pidfile.write("0\n")
        self.options = options
        self.cn_k = 0
    
    def start(self, sd, **options):

        self.options.update(options)
        
        self.ab_vars = options.get('ab_vars', [])
        
        options['num_vars'] = sd.num_vars
        
        self.cnf = sd.cnf
        self.construct_cardinality_network(**options)
        self.cnf += [self.cnf_cn]

        self.num_vars = max([max(self.cn.vars), sd.num_vars])
        self.num_clauses = sd.num_clauses + len(self.clauses_cn)
        
#        if self.options.get('weighted',False):
#            header = "p wcnf %d %d\n" % (self.num_vars, self.num_clauses)
#            opts = ['-e', '-d', '-ms']
#        else:
        self.cnf += ["\n\n-%d 0\n" % self.cn.vars[self.options.get('max_card',1)]]
        self.num_clauses += 1 
        header = "p cnf %d %d\n" % (self.num_vars, self.num_clauses)
        opts = ['-e', '-d']

        with open(self.get_input_file_name(), "w") as f:
            f.write(header)
            for clauses in self.cnf:
                f.write(clauses)
                
        t0 = time.time()
        p = subprocess.Popen([YICES_EXECUTABLE_PATH] + opts, stdin=PIPE, stdout=PIPE)
        
        pidfile.seek(0)
        pidfile.write(str(p.pid) + "\n")
        out, unused_err = p.communicate(header + " " + " ".join(self.cnf))
        
        pidfile.seek(0)
        pidfile.write("0\n")
        t1 = time.time()
        self.solver_time = t1-t0
        self.outlines = out.strip().split("\n")
        self.result = self.parse_output(self.outlines)

    def start_again(self, sd, **options):
        return self.start(sd, **options)

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
            self.clauses_cn = self.cn.card(range(len(ab_vars_padded)), k)
            self.cnf_cn += "\n"
            for c in self.clauses_cn:
                self.cnf_cn += "\n" + " ".join(map(str, c+[0]))
                

    
## ================================================================================================================= ##

SENTENCE_INTERPRETERS_CN = {}
            
class YicesCnEngine(Engine):
    
    def __init__(self, options):
        super(YicesCnEngine, self).__init__(options)
        
        self.sentence_interpreters.update(SENTENCE_INTERPRETERS_CN)
        
        self.cnf = ""
        self.cnf_cn = ""
        self.vars = {}
        self.cn_k = 0
        self.stats = {}
        
    def to_dimacs_literal(self, literal, variable_map):
        if literal.sign == True:
            return str(variable_map.get_key(literal.name)+1)
        else:
            return "-" + str(variable_map.get_key(literal.name)+1)
    
    def to_dimacs_clause(self, clause, variable_map):
        literals = map(lambda l: self.to_dimacs_literal(l, variable_map), clause.literals)
        return " ".join(literals) + " 0"

    def start_again(self, new_sentences, **options):
        super(YicesCnEngine, self).start_again(new_sentences, **options)
        clauses = self.interpret_sentences(new_sentences)
        for c in clauses:
            self.cnf += "\n" + self.to_dimacs_clause(c, self.vars)
        self.stats['cnf_clauses'] += len(clauses)
            
        self.construct_cardinality_network(**options)
        
        self.stats['num_rules'] = self.stats.get('cnf_clauses',0) + self.stats.get('net_clauses',0) + 1
        self.stats['num_vars']  = max(self.cn.vars)

#        cnf  = "p cnf %d %d\n" % (self.stats['num_vars'], self.stats['num_rules']) + self.cnf + self.cnf_cn
        cnf = self.cnf + self.cnf_cn
        cnf += "\n\n-%d 0\n" % self.cn.vars[options.get('max_card',1)] 

        p = SimpleYicesWrapper()
        p.start(SimpleDescription(cnf, self.stats['num_vars'], self.stats['num_rules']))
        self.result = self.parse_output(p.outlines, self.vars, self.ab_vars)
        return self.result
    
    def start(self, description=None, **options):
        super(YicesCnEngine, self).start(description, **options)
        
        if not self.cnf:
            vars = sorted(self.description.get_variables(), key=lambda x: not x.name.startswith("AB"))
            self.vars = TwoWayDict(dict((i, v.name) for i,v in enumerate(vars)))
            self.ab_vars = [i for i,n in self.vars.iteritems() if n.startswith("AB")]
            sentences = self.description.get_sentences()
            for v in self.description.get_variables():
                if v.value is not None:
                    sentences.append(Clause([Literal(v.name, v.value)])) 
            self.core_map = {}
            self.clauses = self.interpret_sentences(sentences)
            
            for c in self.clauses:
                self.cnf += "\n" + self.to_dimacs_clause(c, self.vars)
            
            self.stats['cnf_clauses'] = len(self.clauses)

        self.construct_cardinality_network(**options)

        self.stats['num_rules'] = self.stats.get('cnf_clauses',0) + self.stats.get('net_clauses',0) + 1
        self.stats['num_vars']  = max(self.cn.vars)

#        cnf  = "p cnf %d %d\n" % (self.stats['num_vars'], self.stats['num_rules']) + self.cnf + self.cnf_cn
        cnf = self.cnf + self.cnf_cn
        cnf += "\n\n-%d 0\n" % self.cn.vars[options.get('max_card',1)] 
        
        p = SimpleYicesWrapper()
        p.start(SimpleDescription(cnf, self.stats['num_vars'], self.stats['num_rules']))
        
        self.result = self.parse_output(p.outlines, self.vars, self.ab_vars)
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
#            print "constructing CN in yices"
            net_clauses = self.cn.card(range(len(ab_vars_padded)), k)
            self.cnf_cn += "\n"
            for c in net_clauses:
                self.cnf_cn += "\n" + " ".join(map(str, c+[0]))
            self.stats['net_clauses'] = self.stats.get('net_clauses',0) + len(net_clauses)
        

    def interpret_sentences(self, sentences):
        interpreted_sentences = []
        for s in sentences:
            if type(s) in self.sentence_interpreters:
                interpreted_sentences.extend(self.interpret_sentence(s))
            else:
                interpreted_sentences.append(s)
        return interpreted_sentences

    def interpret_sentence(self, sentence):
        if type(sentence) == Clause:
            return [sentence]
        else:
            sentences = self.sentence_interpreters[type(sentence)](self, sentence, self.vars)
            result = []
            for s in sentences:
                if type(s) != Clause:
                    result.extend(self.interpret_sentence(s))
                else:
                    result.append(s)
            return result

    def register_core_sentence(self, id, sentence):
        self.core_map[id] = sentence

    def parse_output(self, output_lines, variable_map, ab_vars):
        if(output_lines[0] == 'sat'):
            output_values = []
            assignment = output_lines[1]
            for v in assignment.split(" "):
                var_num = int(v.strip("-"))-1
#                print var_num
                if var_num == -1 :
                    break
                elif var_num in self.ab_vars and not v.startswith("-"):
                    output_values.append(variable_map[var_num][3:])
            return output_values
        elif(output_lines[0] == 'unsat'):
            return None
        else:
            print "Uh oh! this one is neither SAT nor UNSAT?"
            print output_lines


SENTENCE_INTERPRETERS[ClauseSentence] = lambda engine, sentence, unused: sentence.to_yices(engine)
SENTENCE_INTERPRETERS[WeightSentence] = lambda engine, sentence, unused: sentence.to_yices(engine)
SENTENCE_INTERPRETERS[BlockingClauseSentence] = lambda engine, sentence, unused: sentence.to_yices(engine)


class YicesException(Exception):
    pass
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()


