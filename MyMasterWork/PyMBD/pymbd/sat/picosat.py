from clause import Clause
from engine import ENGINES, Engine
from literal import Literal
from result import Result
from subprocess import PIPE
from ..util.two_way_dict import TwoWayDict
import os
import random
import subprocess
import time
import mmap

ENGINES['picosat'] = lambda o: PicoSatEngine(o)

def to_dimacs_literal(literal, variable_map):
    if literal.sign == True:
        return str(variable_map.get_key(literal.name)+1)
    else:
        return "-" + str(variable_map.get_key(literal.name)+1)

def to_dimacs_clause(clause, variable_map):
    literals = map(lambda l: to_dimacs_literal(l, variable_map), clause.literals)
    return " ".join(literals) + " 0"

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

PICOSAT_PATH        = os.path.dirname(os.path.abspath(__file__)) + '/../../lib/picosat'
PICOSAT_EXECUTABLE  = PICOSAT_PATH + '/picosat'
PICOSAT_PIDFILE     = PICOSAT_PATH + '/pid'

if not os.path.exists(PICOSAT_PIDFILE):
    with open(PICOSAT_PIDFILE, "w") as f:
        f.write("0\n" + "0"*100+"\n")
        
file = open(PICOSAT_PIDFILE, "r+")
size = os.path.getsize(PICOSAT_PIDFILE)
pidfile = mmap.mmap(file.fileno(), size)

class PicoSatWrapper():
    
    """
    A very low-level PicoSAT wrapper which takes a CNF (as string), writes it to a file and 
    then calls the PicoSAT binary on it, with options defining if an unsat core gets calculated. 
    At the end, the output is interpreted and converted to to a list.  
    """
    
    def __init__(self):
        self.cnf = None
        self.outlines = None
        self.result = None
        self.get_valuation = False
        self.calculate_unsat_core = False
        self.solver_time = 0
        pidfile.seek(0)
        pidfile.write("0\n")
    
    def start(self, header, cnf=[], calculate_unsat_core=False, get_valuation=False):
        """
        You can pass the CNF strings in two ways:
        1) if the string is already concatenated and includes the header, pass it as the first parameter
        2) if you have multiple strings (e.g. because some are updated and some not), you do not have 
        to concatenate them (uses much memory if the CNFs are very large), you pass the header as the 
        first parameter and a list of strings as the second. Then those strings will get written to 
        the file separately without needing to concatenate them first.
        
        For performance reasons you should make sure that the input and output files used here are written 
        to a ramdisk, otherwise the interface will result in penalty due to the file accesses on the disk.    
        """
        self.cnf = cnf
#        print cnf
        self.calculate_unsat_core = calculate_unsat_core
        self.get_valuation = get_valuation
        
        if os.path.exists(self.get_input_file_name()):
            os.remove(self.get_input_file_name())
        if os.path.exists(self.get_output_file_name()):
            os.remove(self.get_output_file_name())
        if os.path.exists(self.get_core_file_name()):
            os.remove(self.get_core_file_name())
        
        with open(self.get_input_file_name(), "w") as f:
            f.write(header)
            for clauses in cnf:
                f.write(clauses)
#                f.write(" ".join(map(str, clauses)) + " 0\n")
#                for c in clauses:
#                    f.write(str(c)+" ")
#                f.write("0\n")
                
                
#        time.sleep(0.05)
        t0 = time.time()
        p = subprocess.Popen([PICOSAT_EXECUTABLE] + self.get_picosat_opts() + [self.get_input_file_name()], stdout=PIPE)
        
        pidfile.seek(0)
        pidfile.write(str(p.pid) + "\n")
#        print p.pid
#        time.sleep(10)
        p.communicate()
        
        pidfile.seek(0)
        pidfile.write("0\n")
        t1 = time.time()
        self.solver_time = t1-t0
#        print self.solver_time
#        time.sleep(0.05)
        with open(self.get_output_file_name(), "r") as f:
            self.outlines = f.read().strip().split("\n")
    
    def get_output(self):
        self.result = self.parse_output(self.outlines, self.get_valuation, self.calculate_unsat_core)
        return self.result
            
    def parse_output(self, output_lines, get_valuation=False, calculate_unsat_core=False):
        if output_lines[0][2:] == 'SATISFIABLE':
            output_values = []
            if get_valuation:
                # get values from remaining lines
                # be aware that only the last line is 0-terminated!
                for l in output_lines[1:]:
                    for v in l.split(" ")[1:]:
                        if v == "0":
                            break
                        output_values.append(int(v))
            return (True, output_values)
        elif output_lines[0][2:] == 'UNSATISFIABLE':
            core = []
            if calculate_unsat_core:
                with open(self.get_core_file_name(), "r") as f:
                    corelines = f.read().strip().split("\n")[1:]
                for l in corelines:
                    core.append(map(int,l.split(" ")[:-1]))
            return (False, core)
        else:
            raise RuntimeError("picosat returned unexpected output: " + "\n".join(output_lines))
    
    def get_input_file_name(self):
        return PICOSAT_PATH + '/picosat.in'
    
    def get_output_file_name(self):
        return PICOSAT_PATH + '/picosat.out'
    
    def get_core_file_name(self):
        return PICOSAT_PATH + '/picosat.core'
    
    def get_picosat_opts(self):
        opts = []
        if self.calculate_unsat_core:
            opts.extend(['-c', self.get_core_file_name()])
        opts.extend(['-o', self.get_output_file_name()])
        opts.extend(['-s', str(random.randint(1,999))])
        return opts
    
class PicoSatEngine(Engine):
    
    """
    This is a high-level PicoSAT wrapper intended for the problem/description/engine/result mechanism in this 
    ``sat'' package. As such, it requires a description containing sentences and variables which will then 
    be converted to a CNF using the corresponding (registered) interpreters. For example, the ISCAS benchmark 
    framework contains sentences and interpreters for Boolean gates. 
    
    If the CNF has been constructed, it calls the low-level PicoSAT wrapper above. 
    """
    
    def __init__(self, options):
        super(PicoSatEngine, self).__init__(options)
        self.sentence_interpreters.update(SENTENCE_INTERPRETERS)
        self.variable_interpreters.update(VARIABLE_INTERPRETERS)
        self.cnf = None
        self.vars = {}
        
    def start(self, description=None, **options):
        super(PicoSatEngine, self).start(description, **options)
        if not self.cnf:
            self.vars = TwoWayDict(dict((i, v.name) for i,v in enumerate(self.description.get_variables())))
            
            # add clauses for the input/output variables which are constrained
            sentences = self.description.get_sentences()
            for v in self.description.get_variables():
                if v.value is not None:
                    sentences.append(Clause([Literal(v.name, v.value)])) 
            self.core_map = {}
            self.clauses = self.interpret_sentences(sentences)
            self.cnf = "p cnf %d %d" % (max(self.vars.keys())+1, len(self.clauses))
            for c in self.clauses:
                self.cnf += "\n" + to_dimacs_clause(c, self.vars)
        
#        print self.cnf
         
        p = PicoSatWrapper()
        p.start(self.cnf, calculate_unsat_core=True)
        
#        print "\n".join(outlines)
        
        self.result = self.parse_output(p.outlines, self.vars, p.get_core_file_name())
        return self.result

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

    def parse_output(self, output_lines, variable_map, core_file_name=None):
        if output_lines[0][2:] == 'SATISFIABLE':
            # get values from remaining lines
            # be aware that only the last line is 0-terminated!
            output_values = {}
            for l in output_lines[1:]:
                for v in l.split(" ")[1:]:
                    var_num = int(v.strip("-"))-1
                    if var_num == -1 or var_num not in variable_map:
                        break
                    if v.startswith("-"):
                        output_values[variable_map[var_num]] = False
                    else:
                        output_values[variable_map[var_num]] = True
            return Result(True, output_values, [])
        elif output_lines[0][2:] == 'UNSATISFIABLE':
            core = []
            if self.options.get('calculate_unsat_core', True) != False:
                with open(core_file_name, "r") as f:
                    corelines = f.read().strip().split("\n")[1:]
                for l in corelines:
                    literals = l.split(" ")[:-1]
                    if len(literals) == 1:  # watching out for clauses with one literal
                        index = abs(int(literals[0]))-1
                        var = self.vars[index]
                        if var in self.core_map:
                            core.append(self.core_map[var].ab_predicate)
            return Result(False, [], core)
        else:
            raise RuntimeError("picosat returned unexpected output: " + "\n".join(output_lines))


    
