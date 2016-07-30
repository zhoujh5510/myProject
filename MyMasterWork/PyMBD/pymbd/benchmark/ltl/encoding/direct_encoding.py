from collections import defaultdict
from ..ltlparser.ast import Type, get_all_subformulas, syntactic_equivalent, Node, \
    BoolOr, BoolXor, WeakUntil, Identifier, get_all_subformulas_list, \
    InstrumentationMode
from ..ltlparser.rewriting import rewrite_to_dag
from ..ltlparser.util.helper import flatten
from pymbd.sat.description import SimpleDescription
# from pymbd.sat.minisat import MiniSatWrapper
from pymbd.sat.picosat import PicoSatWrapper
from pymbd.sat.problem import Problem
# from pymbd.sat.z3smt import Z3ClauseWrapper, Z3DimacsWrapper
from pymbd.util.irange import irange
from trace import Trace
from pymbd.util.two_way_dict import TwoWayDict
import math
import random
import sys
import time

clauses_to_dimacs = lambda s: "\n".join(map(lambda c:" ".join(map(str, c+[0])), s)) + "\n"
class Range(object):
    __slots__ = ['lower', 'upper']
    def __init__(self, lower, upper):
        self.lower, self.upper = lower, upper
    def __contains__(self, item):
        return self.lower <= item < self.upper
    def __repr__(self):
        return "Range(%d,%d)"%(self.lower,self.upper)
    def __iter__(self):
        return iter(xrange(self.lower, self.upper))

class DirectEncoding(object):
    
    """
    This class encodes a given LTL formula and a corresponding trace directly into a SAT problem, which 
    is satisfiable if and only if the formula is satisfied by the trace. To this intent, each subformula 
    is instantiated over time (i.e. ranging over the trace length) and the resulting SAT variables are 
    connected according to the LTL semantics. 
    """
    
    def __init__(self, formula, trace, exclude_traces=set(), **fault_mode_opts):
        
        """
        initialize the object. 
        for timing reasons, this method just assigns a few attribute values, all analyses are done on the first
        call on a check* or get_conflict* method. The meanings of the flags are as follows:
        * instrument_trace: obviously enables/disables the instrumentation for the trace, which means that 
          currently one additional health variable for each signal/time point is created
        * instrument_formula: same for the formula. note that only one of these flags should probably be on 
          for a meaningful diagnosis. instrument_formula is the default
        * instantiate_identifiers: if this is false, identifiers are assumed to be correct and every reference 
          to an identifier in the formula directly refers to the corresponding signal. if this is true, an 
          additional health variable for each occurrence of an identifier is created, which enables us to add 
          the "typo" fault mode.  
        """
        
        self.formula = formula
#        sf = get_all_subformulas(self.formula, Type.ANY)
#        for i in sf:
#            if i.type in [Type.Equivalent, Type.Implies, Type.BoolXor]:
#                raise Exception("Error: you must call rewrite_extended_booleans() on the given formula before calling!")
#            for j in sf:
#                if i != j and syntactic_equivalent(i,j):
#                    raise Exception("Error: you must call rewrite_to_dag() on the given formula before calling!")
        
        # the trace has timesteps 0, 1, ..., K, thus K+1 steps in total
        self.trace = trace
        self.trace_len = len(trace) 
        self.trace_K = len(trace)-1
        
        # the point where the loop begins, i.e. <0,1,..2,L-1><L,L+1,...,K>
        self.trace_L = len(self.trace.stem)
        
        self.subformulae_nodes = None
        self.subformulae = None
        self.var_nodes = None
        self.num_subformulae = 0
        self.offset = 10
        self.last_var_num = 0
        self.stats = {}
        self.initialized = False
        self.initialized_direct = False
        self.fault_modes = {}
        self.fault_vars  = {}
        self.fault_reversemap = {}
        self.fault_mode_opts = fault_mode_opts
        self.instantiate_identifiers = (fault_mode_opts.get('variable_typos', False) or fault_mode_opts.get('literal_not_insertion', False) or fault_mode_opts.get('all', False))
        self.instrument_trace = fault_mode_opts.get('instrument_trace',False)
        self.instrument_formula = fault_mode_opts.get('instrument_formula', True)
        self.trace_vars = TwoWayDict()
        self.formula_vars_range = None
        self.trace_vars_range = None
        self.exclude_traces = exclude_traces
        self.sat_problem = None
        
    def build_sd(self, convert_to_cnf=True):
        """
        
        The clauses are stored as lists of integer numbers, e.g. [1, -4, 5] would be a clause, where negative numbers 
        denote negated literals and the variables start with 1 (this is the convention used in the DIMACS format as 
        used in most SAT solvers). A CNF is a list of integer lists. 
        
        The variable numbers are assigned as follows: 
        Block 1) Health variables
        Block 2) Time-instantiated subformulae variables
        
        Example:  formula is "F(a or b)", trace is <!a,!b;!a,!b><a> (3 time steps). 
                  We assume that variable_typos are enabled, which would result in the following fault modes:
                  (a || b):   [(a || b), (a && b), (a ^  b), (a => b), (a == b), False, False, False]
                  b:          [b, a]
                  a:          [a, b]
                  F(a || b):  [F(a || b), G(a || b), X(a || b), False]
                  (where False denotes deactivated fault modes to end up at a power of 2 fault modes)
                  
        Block 1:  F(a || b): [1, 2], (a || b): [3, 4, 5], a: [6], b: [7]
                  (i.e. variable 1 and 2 are needed to encode the four fault modes for the F subformula, ...)
        Block 2:  F(a || b) |   8 |  14 ||  20
                  (a || b)  |   9 |  15 ||  21
                  a         |  10 |  16 ||  22
                  b         |  11 |  17 ||  23
                  ----------------------------
                  a         |  12 |  18 ||  24
                  b         |  13 |  19 ||  25
                  This means that variables 8 to 23 are used for the time-instantiated subformulae variables 
                  and variables 12 to 25 are used for the signal (trace) variables. 
                  
        The CNF then relates, for example, the two arguments of the OR with its result using the equivalent 
        of 9 = 10 OR 11, 15 = 16 OR 17 and 21 = 22 OR 23. The corresponding fault mode is added (in negated form)
        to those clauses, which would result in the following CNF for the OR node:
        
        [9, -10, 3, 4, 5],  [9, -11, 3, 4, 5],  [-9, 10, 11, 3, 4, 5], 
        [15, -16, 3, 4, 5], [15, -17, 3, 4, 5], [-15, 16, 17, 3, 4, 5], 
        [21, -22, 3, 4, 5], [21, -23, 3, 4, 5], [-21, 22, 23, 3, 4, 5]
        
        where 3,4,5 encodes the assumption that the OR operator is correct in this place (fault mode -3, -4, -5
        added in negated form) 
        
        """
        t0 = time.time()
        
        # all unique nodes representing subformulae of the given formula
        self.identifier_nodes  = get_all_subformulas_list(self.formula, Type.Identifier)
        if self.instantiate_identifiers:  
            self.subformulae_nodes = get_all_subformulas_list(self.formula, Type.ANY)
        else:
            self.subformulae_nodes = get_all_subformulas_list(self.formula, lambda n: n.type != Type.Identifier)

#        for s in self.subformulae_nodes:
#            print s.id, s

        # a mapping of the subformulae_nodes to the integer range 1...len(subformulae_nodes)
        num_range = range(1, len(self.subformulae_nodes)+1)
#        if self.exclude_traces: # we want to generate different traces, so shuffle subformulas too
#            random.shuffle(num_range)

        self.subformulae = TwoWayDict(dict(zip(map(lambda n: n.id, self.subformulae_nodes),num_range)))
        
        # a mapping from variable name (e.g. "a") to the node in subformulae_nodes
        self.var_nodes = defaultdict(list)
        for n in self.identifier_nodes:
            self.var_nodes[n.value].append(n)
            
        # add those variables not in the formula but only in the trace (may be needed for fault mode diagnosis)
        if self.instantiate_identifiers:
            for step in self.trace.stem.children + self.trace.loop.children:
                for v in step:
                    if v.type == Type.BoolNot and v.i.type == Type.Identifier and v.i.value not in self.var_nodes:
                        self.var_nodes[v.i.value].append(v.i)
                    elif v.type == Type.Identifier and v.value not in self.var_nodes:
                        self.var_nodes[v.value].append(v)
                    else:
                        pass

        # a mapping from variable name (e.g. "a") to their variable numbers in the first time step 
        self.signals = TwoWayDict(dict(zip(self.var_nodes.keys(),xrange(max(self.subformulae.values())+1, sys.maxint))))
        
        # the number of unique subformulae
        self.num_subformulae = len(self.subformulae_nodes)
        self.num_signals = len(self.signals)
        
        self.time_step_increase = self.num_subformulae + self.num_signals
        #print self.num_vars()
        next_mode_var_num = 1
        
        for sf in self.subformulae_nodes:
            if self.create_fault_modes(sf, **self.fault_mode_opts):
                num_vars_needed = int(math.ceil(math.log(len(self.fault_modes[sf]),2)))
                #print "num_vars_needed:", num_vars_needed
                self.fault_vars[sf] = range(next_mode_var_num, next_mode_var_num+num_vars_needed)
                for v in self.fault_vars[sf]:
                    self.fault_reversemap[v] = (sf,v-next_mode_var_num,num_vars_needed)
                next_mode_var_num += num_vars_needed
        
        self.formula_vars_range = Range(1, next_mode_var_num)
        
        # simple trace instrumentation: one variable for each signal/time-step combination
        if self.instrument_trace:
            for s in self.signals:
                for i in xrange(self.trace_len):
                    self.trace_vars[s,i] = next_mode_var_num
                    next_mode_var_num += 1
        
#        for s in self.trace_vars:
#            print s, self.trace_vars[s]
        
        self.trace_vars_range = Range(self.formula_vars_range.upper, next_mode_var_num)
#        print self.formula_vars_range
#        print self.trace_vars_range
        
        # offset is the first variable used for the time instantiated subformula variables
        self.offset = next_mode_var_num - 1

        self.last_var_num = (self.offset + self.time_step_increase*self.trace_len)
        
        self.num_vars_in_loop = ((self.trace_K-self.trace_L+1)*self.time_step_increase)
    
        self.clauses = []
        
        # determine the number of health variables needed for a subformula and assign 
        # the variables to the corresponding subformula
        for sf in self.fault_modes:
#            print sf
            digits = xrange(0,int(math.ceil(math.log(len(self.fault_modes[sf]),2))))
            for fm_num, sf_mode in enumerate(self.fault_modes[sf]):
                fault_mode = [-self.fault_vars[sf][i] if fm_num & 1<<i else self.fault_vars[sf][i] for i in digits]
#                print fault_mode, "->", sf_mode
                if sf_mode == False:
#                    print "blocking fault mode", fm_num, fault_mode
                    self.clauses += [fault_mode]
                elif sf_mode == True:
                    pass
                else:
                    self.clauses += self.clauses_for_formula(sf_mode, fault_mode)    
        
        self.clauses_sd = self.clauses
        if convert_to_cnf: 
            self.cnf_sd = clauses_to_dimacs(self.clauses)
        t1 = time.time()
        self.stats['enc_time_spec'] = t1-t0
    
    def build_trace(self, convert_to_cnf=True):
        t0 = time.time()
        self.clauses_t = self.clauses_for_trace()
        if convert_to_cnf:
            self.cnf_t = clauses_to_dimacs(self.clauses_t)
        t1 = time.time()
        self.stats['enc_time_trace'] = t1-t0
    
    def clauses_for_trace(self):
        """
        construct the (unit) clauses fixing the trace values. 
        """
        clauses = []
        for i,step in enumerate(self.trace.stem.children + self.trace.loop.children):
            for v in step:
                if v.type == Type.BoolNot and v.i.type == Type.Identifier:
                    signal, polarity = v.i.value, -1
                elif v.type == Type.Identifier:
                    signal, polarity = v.value, +1
                if signal in self.signals:
#                    print "Signal", signal
                    clause = [polarity * self.num(signal, i)]
                    if self.instrument_trace and (signal,i) in self.trace_vars:
                        clause += [self.trace_vars[signal,i]]
                    clauses += [clause]
#                else:
#                    print "Signal", signal, "not constrained by formula?"
        return clauses
    
    def clause_for_excluded_trace(self, trace):
        """
        construct the clauses for the traces which should be prohibited as the next solution when computing/completing traces (witnesses)
        """
        clause = []
        for i,step in enumerate(trace.stem.children + trace.loop.children):
            for v in step:
                if v.type == Type.BoolNot and v.i.type == Type.Identifier:
                    signal, polarity = v.i.value, +1
                elif v.type == Type.Identifier:
                    signal, polarity = v.value, -1
                if signal in self.signals:
                    clause += [polarity * self.num(signal, i)]
        return clause
    
    def build_all(self, abnormal_subformulae, abnormal_trace_points, convert_to_cnf=True):
        """
        construct the CNF for the system (formula) and trace if not already done. 
        construct the CNF for the health assignments from abnormal_subformulae and abnormal_trace_points 
        for calculations without fault modes. 
        """
        if not self.initialized:
            self.build_sd()
            self.build_trace()
#            self.initialized = True
        
        t0 = time.time()
        self.clauses_modes = []
        for sf in self.fault_modes:
            if sf not in abnormal_subformulae:
                self.clauses_modes += [[-self.fault_vars[sf][i]] for i in range(len(self.fault_vars[sf]))]
            
        if self.instrument_trace:
            for s in self.signals:
                for i in range(self.trace_len):
                    if (s,i) not in abnormal_trace_points:
                        self.clauses_modes += [[-self.trace_vars[s,i]]]
        
        if convert_to_cnf:
            self.cnf_modes = clauses_to_dimacs(self.clauses_modes)
        t1 = time.time()
        self.stats['enc_time_spec'] += t1-t0
        
    
    
    def check(self, calculate_unsat_core=False, abnormal_subformulae=[], abnormal_trace_points=[], get_valuation=True, trace_for_unsat=False, sat_solver=None, config={}):
        """
        consistency check without fault modes (only binary health variables)
        for the subformulae in abnormal_subformulae, the health variable is set to false (=ABNORMAL) (or equally, for the trace points in abnormal_trace_points)
        in the computed CNF. 
        
        If the trace is not fully specified, this method can also be used to complete a trace, in which case get_valuation should definitely be left True. 
        To compute different traces for a formula, the exclude_traces attribute can be used to exclude a list of previously computed traces, which are then 
        prohibited for the new solution.
        
        The CNF for the system description (obtained from the formula), the trace, the mode assignments (health variables) and the excluded traces are 
        stored separately, because parts are reused in consecutive calls while others have to be regenerated. 
        
        Depending on the SAT solver to be used, the CNF clause list and CNF string itself are handled slightly differently. For picosat, a string has to be 
        generated for each part of the CNF, but for performance reasons, these strings are not concatenated but passed as a list of strings to the solver 
        wrapper. In this case the number of clauses is computed by adding the lengths of the various parts.  For minisat, the clauses can be passed directly 
        as integer lists. 
        """
        self.build_all(abnormal_subformulae, abnormal_trace_points)
        
        clauses_exclude_traces = []
        if self.exclude_traces:
            for t in self.exclude_traces:
                clauses_exclude_traces += [self.clause_for_excluded_trace(t)]
        
        if sat_solver == None or sat_solver == 'picosat':
            self.num_clauses = len(self.clauses_sd) + len(self.clauses_t) + len(self.clauses_modes) + 1 + len(clauses_exclude_traces)
            # print len(self.clauses_sd), len(self.clauses_t), len(self.clauses_modes), 1, len(clauses_exclude_traces)
            cnf = [self.cnf_sd, self.cnf_t, self.cnf_modes, clauses_to_dimacs([[self.num(self.formula,0)]]), clauses_to_dimacs(clauses_exclude_traces)]
            self.sat, self.output = self.solve_sat(cnf, self.num_vars(), self.num_clauses, calculate_unsat_core=calculate_unsat_core, get_valuation=get_valuation)
        elif sat_solver.startswith('minisat'):
            clauses = self.clauses_sd + self.clauses_t + self.clauses_modes + [[self.num(self.formula,0)]] + clauses_exclude_traces
            self.sat, self.output = self.solve_sat_minisat(clauses, sat_solver=sat_solver)
        elif sat_solver == 'z3-clause':
            clauses = self.clauses_sd + self.clauses_t + self.clauses_modes + [[self.num(self.formula,0)]] + clauses_exclude_traces
            self.sat, self.output = self.solve_sat_z3clause(clauses, sat_solver=sat_solver)
        elif sat_solver == 'z3-dimacs':
            num_clauses = len(self.clauses_sd) + len(self.clauses_t) + len(self.clauses_modes) + 1 + len(clauses_exclude_traces)
            # print len(self.clauses_sd), len(self.clauses_t), len(self.clauses_modes), 1, len(clauses_exclude_traces)
            cnf = [self.cnf_sd, self.cnf_t, self.cnf_modes, clauses_to_dimacs([[self.num(self.formula,0)]]), clauses_to_dimacs(clauses_exclude_traces)]
            self.sat, self.output = self.solve_sat_z3dimacs(cnf, self.num_vars(), num_clauses, calculate_unsat_core=calculate_unsat_core, get_valuation=get_valuation)
             
        if not self.sat and trace_for_unsat == True:
            if sat_solver == None or sat_solver == 'picosat':
                cnf = [self.cnf_sd, self.cnf_t, self.cnf_modes, clauses_to_dimacs([[-self.num(self.formula,0)]])]
                num_clauses = len(self.clauses_sd) + len(self.clauses_t) + len(self.clauses_modes) + 1
                _, out = self.solve_sat(cnf, self.num_vars(), num_clauses, calculate_unsat_core=False, get_valuation=True)#, sat_solver=sat_solver)
                self.result = (self.sat, self.get_trace(out))
            elif sat_solver.startswith('minisat'):
                _, out = self.solve_sat_minisat(clauses, sat_solver=sat_solver)
                
        
        self.stats['total_time'] = self.stats['enc_time_spec'] + self.stats['enc_time_trace'] + self.stats['solver_time']

        self.result = (self.sat, self.output)
        return self.sat

    def get_conflict(self, abnormal_subformulae=[], abnormal_trace_points=[], sat_solver=None, config={}):
        """
        compute a new conflict set without fault modes (only binary health variables)
        """
        self.build_all(abnormal_subformulae, abnormal_trace_points)
        if sat_solver == None or sat_solver == 'picosat':
            cnf = [self.cnf_sd, self.cnf_t, self.cnf_modes, clauses_to_dimacs([[self.num(self.formula,0)]])]
            num_clauses = len(self.clauses_sd) + len(self.clauses_t) + len(self.clauses_modes) + 1
            self.sat, self.output = self.solve_sat(cnf, self.num_vars(), num_clauses, calculate_unsat_core=True, get_valuation=True)
            if not self.sat:
                modes_f = sorted([f[0] for f in self.output if len(f) == 1 and abs(f[0]) in self.formula_vars_range],key=abs)
                modes_t = sorted([f[0] for f in self.output if len(f) == 1 and abs(f[0]) in self.trace_vars_range],key=abs)

        elif sat_solver == 'z3-clause':
            clauses = self.clauses_sd + self.clauses_t + [[self.num(self.formula,0)]]
            self.sat, self.output = self.solve_sat_z3clause(clauses, sat_solver, assumptions=flatten(self.clauses_modes), calculate_unsat_core=True, get_valuation=True)
            if not self.sat:
                modes_f = sorted([f for f in self.output if abs(f) in self.formula_vars_range],key=abs)
                modes_t = sorted([f for f in self.output if abs(f) in self.trace_vars_range],key=abs)
                
        self.stats['total_time'] = self.stats['enc_time_spec'] + self.stats['enc_time_trace'] + self.stats['solver_time']
        
        if not self.sat:
            cs = set()
            for sf in modes_f:
                cs.add(self.fault_reversemap[abs(sf)][0])
                
            for sf in modes_t:
                cs.add(self.trace_vars.get_key(abs(sf)))
            self.result = (self.sat, cs)
        else:
            self.result = (self.sat, [])
        return self.result
    
    def get_conflict_with_modes(self, mode_assignment={}, sat_solver=None):
        """
        compute a new conflict set with fault modes
        """
        t0 = time.time()
        if not self.initialized:
            self.build_sd()
            self.build_trace()
            self.initialized = True
        
        t0_ = time.clock()
        self.clauses_modes = []
        for sf in self.fault_modes:
            if sf not in mode_assignment:
                self.clauses_modes += [[-self.fault_vars[sf][i]] for i in range(len(self.fault_vars[sf]))]
            else:
                digits = xrange(0,int(math.ceil(math.log(len(self.fault_modes[sf]),2))))
                self.clauses_modes += [[self.fault_vars[sf][i]] if mode_assignment[sf] & 1<<i else [-self.fault_vars[sf][i]] for i in digits]
        
        self.cnf_modes = clauses_to_dimacs(self.clauses_modes)
        t1 = time.clock()
        self.stats['enc_time_spec'] += t1-t0_

        if sat_solver == None or sat_solver == 'picosat':
            cnf = [self.cnf_sd, self.cnf_t, self.cnf_modes, clauses_to_dimacs([[self.num(self.formula,0)]])]
            #clauses = self.clauses_sd + self.clauses_t + self.clauses_modes + [[self.num(self.formula,0)]]
            num_clauses = len(self.clauses_sd) + len(self.clauses_t) + len(self.clauses_modes) + 1
            self.sat, self.output = self.solve_sat(cnf, self.num_vars(), num_clauses, calculate_unsat_core=True, get_valuation=True)
    #        self.stats['total_time'] = self.stats['enc_time_spec'] + self.stats['enc_time_trace'] + self.stats['solver_time']
            if not self.sat:
                modes = sorted([f[0] for f in self.output if len(f) == 1 and abs(f[0]) in self.formula_vars_range],key=abs)
        elif sat_solver == 'z3-clause':
            clauses = self.clauses_sd + self.clauses_t + [[self.num(self.formula,0)]]
            self.sat, self.output = self.solve_sat_z3clause(clauses, sat_solver, assumptions=flatten(self.clauses_modes), calculate_unsat_core=True, get_valuation=True)
            if not self.sat:
                modes = sorted([f for f in self.output if abs(f) in self.formula_vars_range],key=abs)


        if not self.sat:
            modes_result = self.extract_modes(modes)
            cs = set(modes_result)
            self.result = (self.sat, cs)
        else:
            self.result = (self.sat, [])
        t1 = time.time()
        self.stats['total_time'] = self.stats.get('total_time',0) + (t1-t0)
        return self.result


    def get_diagnosis(self, sat_solver=None):
        """
        compute an arbitrary diagnosis for the given formula, assuming the trace to be correct. this simply lets all 
        health variables unassigned and to be chosen by the SAT solver. This means that the result must NOT be minimal
        and in fact the SAT solver can choose modes != 0, even if the trace would satisfy the specification originally.  
        """
        if not self.initialized:
            self.build_sd()
            self.build_trace()
            self.initialized = True
        
        self.cnf_modes = ""
        self.clauses_modes = []
        
        cnf = [self.cnf_sd, self.cnf_t, self.cnf_modes, clauses_to_dimacs([[self.num(self.formula,0)]])]
        #clauses = self.clauses_sd + self.clauses_t + self.clauses_modes + [[self.num(self.formula,0)]]
        num_clauses = len(self.clauses_sd) + len(self.clauses_t) + len(self.clauses_modes) + 1
        self.sat, self.output = self.solve_sat(cnf, self.num_vars(), num_clauses, calculate_unsat_core=True, get_valuation=True)
        
        self.stats['total_time'] = self.stats['enc_time_spec'] + self.stats['enc_time_trace'] + self.stats['solver_time']
        
#        self.print_variables()
#        print self.output

        if self.sat:
            modes = sorted([f for f in self.output if abs(f) in self.formula_vars_range],key=abs)
            modes_result = self.extract_modes(modes)
            for m in modes_result:
                new = self.fault_modes[m[0]][m[1]]
                m[0].type = new.type
                m[0].children = new.children
                
            self.result = (self.sat, self.formula)
        else:
            self.result = (self.sat, None)
        return self.result

    def calculate_next_diagnosis(self, blocked_diagnoses, max_card=None, find_all_sols=False, sat_solver=None, config={}):
        
        sfm = (self.fault_mode_opts.get('ab_predicates', False) == False or self.fault_mode_opts.get('all', False) == True)
        yices = sat_solver.startswith("yices-maxsat")
        
        if self.initialized_direct is False:
#            print "Building encoding started at %.6f" % time.time()
            self.initialized_direct = True
            
            self.build_sd(False)
            self.build_trace(False)
            self.clauses = []
            self.clauses_modes = []
            self.clauses_sys = [[self.num(self.formula,0)]]
            self.clauses_aux_ab = []
            self.clauses_opt = []
            self.cnf_opt = ""
            
#            if config.get('pruning',None) == "PruneUp":
            if True:
#                self.formula.propagate_parent()
                for sf in self.fault_vars:
                    parent = sf.parent
                    while parent:
                        self.clauses_opt.append([-self.fault_vars[sf][0], -self.fault_vars[parent][0]]) 
                        parent = parent.parent
                self.cnf_opt = clauses_to_dimacs(self.clauses_opt)
                
            t0 = time.time()
            if sfm:
                # in the SFM case, we need auxiliary (binary) AB predicates which are set to true as soon as a subformula is not 
                # in its nominal mode, this is used to track the cardinality of solutions
                self.aux_ab_vars = {}
                next_var_num = self.last_var_num + 1
                for sf in self.fault_vars:
                    if self.fault_vars[sf]:
                        self.aux_ab_vars[sf] = next_var_num
                        for v in self.fault_vars[sf]:
                            self.clauses_aux_ab.append([next_var_num, -v])
                        next_var_num += 1
            
            # HACK!!!
            if yices:
                self.weighted = True
                self.clauses_modes = []
                
                if sfm:
                    for sf in self.aux_ab_vars:
                        self.clauses_modes += [[-self.aux_ab_vars[sf]]]
                else:
                    for sf in self.fault_modes:
                        self.clauses_modes += [[-self.fault_vars[sf][i]] for i in range(len(self.fault_vars[sf]))]
                    
                for c in self.clauses_sd + self.clauses_t + self.clauses_sys + self.clauses_aux_ab:
                    c.insert(0, 2) # prepend weight of 2 (=infinity) to each clause
                for c in self.clauses_modes:
                    c.insert(0, 1)
            else:
                self.weighted = False
            
            self.cnf_sd, self.cnf_t, self.cnf_modes, self.cnf_sys = map(clauses_to_dimacs, [self.clauses_sd, self.clauses_t, self.clauses_modes, self.clauses_sys])
            self.num_clauses = len(self.clauses_sd) + len(self.clauses_t) + len(self.clauses_modes) + len(self.clauses_sys) 
#            self.clauses_sd, self.clauses_t, self.clauses_modes, self.clauses_sys = (None,None,None,None)
            self.clauses_blocked = []
            self.cnf_blocked = []
            t1 = time.time()
            self.stats['enc_time_spec'] += (t1-t0)
            
#            print "Building encoding finished at %.6f" % time.time()

        if sfm:
                    
            ab_vars = list(self.aux_ab_vars.values())
            self.num_aux_ab_vars = len(ab_vars)
            
            for bd in blocked_diagnoses:
                self.clauses_blocked += [[]]
                for sf,m in bd.iteritems():
                    fault_mode = [-self.fault_vars[sf][i] if m & 1<<i else self.fault_vars[sf][i] for i in xrange(len(self.fault_vars[sf]))]
                    self.clauses_blocked[-1] += fault_mode
                if self.weighted:
                    self.clauses_blocked[-1].insert(0, 2)
                
        else:
            ab_vars = list(self.formula_vars_range)
            self.num_aux_ab_vars = 0
            
            if self.weighted:
                for bd in blocked_diagnoses:
                    self.clauses_blocked += [[2] + [-self.fault_vars[sf][i] for sf in bd for i in range(len(self.fault_vars[sf]))]]
            else:
                for bd in blocked_diagnoses:
                    self.clauses_blocked += [[-self.fault_vars[sf][i] for sf in bd for i in range(len(self.fault_vars[sf]))]]
            
        self.cnf_blocked = clauses_to_dimacs(self.clauses_blocked)
        self.cnf_aux_ab  = clauses_to_dimacs(self.clauses_aux_ab)
        
        if config.get('pruning',None) == "PruneUp":
            cnf = [self.cnf_sd, self.cnf_t, self.cnf_modes, self.cnf_sys, self.cnf_blocked, self.cnf_aux_ab, self.cnf_opt]
            num_clauses = self.num_clauses + len(self.clauses_blocked) + len(self.clauses_aux_ab) + len(self.clauses_opt)
        else:
            cnf = [self.cnf_sd, self.cnf_t, self.cnf_modes, self.cnf_sys, self.cnf_blocked, self.cnf_aux_ab]#, self.cnf_opt]
            num_clauses = self.num_clauses + len(self.clauses_blocked) + len(self.clauses_aux_ab)# + len(self.clauses_opt)
        
#        print "".join(cnf)
        
        sd = SimpleDescription(cnf, self.num_vars() + self.num_aux_ab_vars, num_clauses, get_valuation=True)
        if not self.sat_problem:
            self.sat_problem = Problem(sat_solver)
            r = self.sat_problem.solve(sd, weighted=self.weighted, ab_vars=ab_vars, max_card=max_card, find_all_sols=find_all_sols, max_out=self.formula_vars_range.upper-1)
        else:
            r = self.sat_problem.solve_again(sd, weighted=self.weighted, ab_vars=ab_vars, max_card=max_card, find_all_sols=find_all_sols)
        
        diag = set()
        if not r:
            return diag 
        
        if not find_all_sols:
            r = [r]
        
        if sfm:
            for sol in r:
                d = set()
                modes_vars = defaultdict(list)

                for l in sol:
                    if l in self.formula_vars_range:
                        modes_vars[self.fault_reversemap[abs(l)][0]] += [l]

                for sf in modes_vars:
                    mode_num = sum([1 << i if v in modes_vars[sf] else 0 for i,v in enumerate(self.fault_vars[sf])])
                    d.add((sf,mode_num))
                diag.add(frozenset(d))

        else: # wfm case
            for sol in r:
                d = set()
                for l in sol:
                    if l in self.formula_vars_range and l > 0:
                        d.add(self.fault_reversemap[l][0])
                diag.add(frozenset(d))

        self.stats['enc_total_time'] = self.stats['enc_time_spec'] + self.stats['enc_time_trace']
        self.stats['solver_time'] = 0 # doesn't make any sense
        self.stats['num_vars'] = self.num_vars() + self.num_aux_ab_vars
        self.stats['num_clauses'] = num_clauses
        
        if not find_all_sols:
            return iter(diag).next()
        else:
            return diag
        
        

    def check_with_modes(self, calculate_unsat_core=False, mode_assignment={}, get_valuation=True, trace_for_unsat=False, sat_solver=None):
        """
        consistency check with fault modes
        """
        t0 = time.time()
        if not self.initialized:
            self.build_sd()
            self.build_trace()
            self.initialized = True
        
        t0_ = time.clock()
        self.clauses_modes = []
        for sf in self.fault_modes:
            if sf not in mode_assignment:
                self.clauses_modes += [[-self.fault_vars[sf][i]] for i in range(len(self.fault_vars[sf]))]
            else:
                digits = xrange(0,int(math.ceil(math.log(len(self.fault_modes[sf]),2))))
                self.clauses_modes += [[self.fault_vars[sf][i]] if mode_assignment[sf] & 1<<i else [-self.fault_vars[sf][i]] for i in digits]
        
        self.cnf_modes = clauses_to_dimacs(self.clauses_modes)
        t1 = time.clock()
        self.stats['enc_time_spec'] += t1-t0_
        
        if sat_solver == None or sat_solver == 'picosat':
    #        cnf = self.cnf_sd + self.cnf_t + self.cnf_modes + clauses_to_dimacs([[self.num(self.formula,0)]])
            num_clauses = len(self.clauses_sd) + len(self.clauses_t) + len(self.clauses_modes) + 1
            cnf = [self.cnf_sd, self.cnf_t, self.cnf_modes, clauses_to_dimacs([[self.num(self.formula,0)]])]
            self.sat, self.output = self.solve_sat(cnf, self.num_vars(), num_clauses, calculate_unsat_core=calculate_unsat_core, get_valuation=get_valuation)
        elif sat_solver == 'z3-clause':
            clauses = self.clauses_sd + self.clauses_t + [[self.num(self.formula,0)]]
            self.sat, self.output = self.solve_sat_z3clause(clauses, sat_solver, assumptions=flatten(self.clauses_modes), calculate_unsat_core=calculate_unsat_core, get_valuation=get_valuation)
        
#        self.stats['total_time'] = self.stats['enc_time_spec'] + self.stats['enc_time_trace'] + self.stats['solver_time']

        self.result = (self.sat, [])
        t1 = time.time()
        self.stats['total_time'] = self.stats.get('total_time',0) + (t1-t0)
        
        return self.sat

    def num_vars(self):
        """ 
        the total number of variables for the SAT problem
        """
        return self.offset + self.time_step_increase * self.trace_len

        
    def num(self, var, time_offset=0):
        """
        returns the variable number for a given variable, calculated as outlined in the example above. 
        ``var'' can have several types, which also determines which number is returned (i.e. from the 
        health variable range or the trace range).
        """
        if type(var) == str:
            return self.offset + self.signals[var] + self.time_step_increase * time_offset
        elif var.type == Type.Identifier and not self.instantiate_identifiers:
            return self.offset + self.signals[var.value] + self.time_step_increase * time_offset
        else:
            return self.offset + self.subformulae[var.id] + self.time_step_increase * time_offset

    def solve_sat(self, cnf, num_vars, num_clauses, **options):
        """
        solve the given sat problem using PicoSAT
        """
        s = PicoSatWrapper()
        header = "p cnf %d %d\n" % (num_vars, num_clauses) 
#        print sat_input
        s.start(header, cnf, **options)
        
        self.stats['solver_time'] = self.stats.get('solver_time',0) + s.solver_time
        self.stats['num_clauses'] = num_clauses
        self.stats['num_vars']    = self.num_vars()
        return s.get_output()
    
    def solve_sat_minisat(self, clauses, sat_solver=None, **options):
        """
        solve the given sat problem using MiniSAT
        """
        s = MiniSatWrapper(sat_solver=sat_solver)
        s.start(clauses, **options)
        self.stats['solver_time'] = self.stats.get('solver_time',0) + s.solver_time
        self.stats['num_clauses'] = len(self.clauses)
        self.stats['num_vars']    = self.num_vars()
        return s.get_output()
    
    def solve_sat_z3clause(self, clauses, sat_solver=None, **options):
        """
        solve the given sat problem using Z3 with the python library
        """
        s = Z3ClauseWrapper()
        vars = xrange(1,self.num_vars()+1)
        s.start(vars, clauses, **options)
        self.stats['solver_time'] = self.stats.get('solver_time',0) + s.solver_time
        self.stats['num_clauses'] = len(self.clauses)
        self.stats['num_vars']    = self.num_vars()
        return s.get_output()
    
    def solve_sat_z3dimacs(self, cnf, num_vars, num_clauses, **options):
        """
        solve the given sat problem using Z3 using DIMACS input file
        """
        s = Z3DimacsWrapper()
        header = "p cnf %d %d\n" % (num_vars, num_clauses) 
#        print sat_input
        s.start(header, cnf, **options)
        
        self.stats['solver_time'] = self.stats.get('solver_time',0) + s.solver_time
        self.stats['num_clauses'] = num_clauses
        self.stats['num_vars']    = self.num_vars()
        return s.get_output()
    
    def extract_modes(self, modes):
        # get all the unit clauses referring to a fault mode variable
        modes_vars = defaultdict(list)
        # map the mode assignments to the corresponding sub-formulae
        for cl in modes:
            modes_vars[self.fault_reversemap[abs(cl)][0]] += [cl]
        
        modes_result = []
        # convert the assignment back to a mode number
        for sf in modes_vars:
            if len(modes_vars[sf]) != len(self.fault_vars[sf]):
                raise Exception("Error: The SAT solver did not assign a unique fault mode to %s" % sf)
            mode_num = sum([1 << i if v > 0 else 0 for i,v in enumerate(modes_vars[sf])])      # note: 0 and 1 are inverted due to CNF implication mode->f = !mode v f
#            print "mode result", modes_result[sf], "is mode number", mode_num
            modes_result.append((sf, mode_num))
        return modes_result

    def add_timestep(self, var, timestep):
        """
        adds the given number of timesteps to a variable number ``var'', while taking the 
        trace loop into consideration (anything which exceeds the last time step will be wrapped 
        around to count from the beginning of the loop again). 
        """
        r = abs(var) + self.time_step_increase*timestep
        while r > self.last_var_num:
            r = r - self.num_vars_in_loop
        return cmp(var, 0)*r
    
    def clauses_for_formula(self, f, fault_mode = []):
        """
        This is the main method constructing the CNF clauses for a given formula f, adding the given fault_mode 
        to each clause at the end. 
        
        To understand the encoding rationale and how the clauses are constructed refer to the paper 
        "An LTL SAT Encoding for Behavioral Diagnosis" (Pill and Quaritsch, 2012) Tables 1 and 2. 
        """
        clause_list = []
        
        # read this as follows:    
        # f ... formula, l ... left sub-formula, r ... right sub-formula, "-" ... not
        # i ... inner part (unary operators), num(f, i) ... f_i (i time steps added)
        # e.g. if f <-> a && b, [-num(f), num(f.l), num(f.r)] is the clause (!f || a || b)  
        num = self.num
        add_timestep = self.add_timestep
        K = self.trace_K
        L = self.trace_L
        n = self.time_step_increase    # number to be added for each time-step increase
        
        # for all time-steps, if the prototype clause contains no variable from timestep +1
        # clauses for 0...K can be produced without overflow check  
        # if proto contains a +1, steps 0...K-1 can be created without overflow check, and last two clauses with
        # overflow check (thus using the add_timestep method)
        
        # 0) Constants
        if f.type == Type.Constant:
            if f.value == "True":
                clause_list += [[num(f,i)] for i in irange(0,K)]
            if f.value == "False":
                clause_list += [[-num(f,i)] for i in irange(0,K)]
        
        # 1) AND
        elif f.type == Type.BoolAnd:
            proto = [[-num(f), num(f.l)], [-num(f), num(f.r)], [num(f), -num(f.l), -num(f.r)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K) for c in proto]
            
        # 2) OR    
        elif f.type == Type.BoolOr:
            proto = [[num(f), -num(f.l)], [num(f), -num(f.r)], [-num(f), num(f.l), num(f.r)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K) for c in proto]
        
        # XOR
        elif f.type == Type.BoolXor:
            proto = [[-num(f), -num(f.l), -num(f.r)], [num(f), -num(f.l), num(f.r)], [num(f), num(f.l), -num(f.r)], [-num(f), num(f.l), num(f.r)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K) for c in proto]
        
        # EQUIVALENT
        elif f.type == Type.Equivalent:
            proto = [[num(f), -num(f.l), -num(f.r)], [-num(f), -num(f.l), num(f.r)], [-num(f), num(f.l), -num(f.r)], [num(f), num(f.l), num(f.r)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K) for c in proto]

        # IMPLICATION
        elif f.type == Type.Implies:
            proto = [[-num(f), -num(f.l), num(f.r)], [num(f), num(f.l)], [num(f), -num(f.r)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K) for c in proto]
        
        # 3) NEXT
        elif f.type == Type.Next:
            proto = [[-num(f), num(f.i,+1)], [num(f), -num(f.i,+1)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K-1) for c in proto]
            clause_list += [[add_timestep(v, K) for v in c] for c in proto]
        
        # 4) NOT
        elif f.type == Type.BoolNot:
            proto = [[-num(f), -num(f.i)], [num(f), num(f.i)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K) for c in proto]
        
        # 5) FINALLY    
        elif f.type == Type.Finally:
            # phi <-> F(delta_i)
            # a) and
            # b)
            # forall i: phi_i+1 -> phi_i (incl. phi_L -> phi_K)
            proto = [[-num(f,+1), num(f)], [-num(f.i), num(f)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K-1) for c in proto]
            clause_list += [[add_timestep(v, K) for v in c] for c in proto]
            
            # c) for i = L..K-1: phi_i -> phi_i+1 (incl. phi_K -> phi_L)
            # this is an OPTIONAL clause (i.e. not needed for correctness)
            # proto = [[-num(f), num(f,+1)]]
            # clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(L, K-1) for c in proto]
            # clause_list += [[add_timestep(v, K) for v in c] for c in proto]
            
            # d) phi_L -> \bigvee_(L<=i<=K): (delta_i)cr
            clause_list += [[-num(f,L)] + [num(f.i, i) for i in irange(L,K)]]   # timesteps are fixed -> no add_timestep
            
            # e) forall 0<=i<L: phi_i -> (delta_i or phi_i+1)
            proto = [[-num(f), num(f.i), num(f,+1)]]
            #  no add_timestep, because dealing with stem
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, L-1) for c in proto]
            
        # 6) GLOBALLY
        elif f.type == Type.Globally:
            # phi <-> G(delta_i)
            # a) - c)
            # phi_i -> delta_i, phi_i -> phi_i+1, !phi_i -> (!delta_i | !phi_i+1)
            proto = [
                     [-num(f), num(f.i)],               # a)
                     [-num(f), num(f,+1)],              # b)
                     [num(f), -num(f.i), -num(f,+1)]    # c)
                    ]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K-1) for c in proto]
            clause_list += [[add_timestep(v, K) for v in c] for c in proto]
            
            # d) is redundant (see b) !phi_i+1 -> !phi_i 
            # e) is redundant (see a)
            # f) !phi_K -> \bigvee_(L<=i<=K) !delta_i   
            clause_list += [[num(f,K)] + [-num(f.i, i) for i in irange(L,K)]] # timesteps are fixed -> no add_timestep
                        
        # 7) UNTIL and WEAKUNTIL
        elif f.type == Type.Until or f.type == Type.WeakUntil:
            # phi <-> delta U sigma
            # a) forall i: phi_i -> (sigma_i || (delta_i && phi_i+1)) (expansion rule)
            # b) forall i: sigma_i -> phi_i
            # c) forall i: (delta_i && phi_i+1) -> phi_i
            #        a)                                                             b)                   c)
            proto = [
                     [-num(f), num(f.r), num(f.l)], [-num(f), num(f.r), num(f,+1)], 
                     [-num(f.r), num(f)], 
                     [-num(f.l), -num(f,+1), num(f)]
                    ]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K-1) for c in proto]
            clause_list += [[add_timestep(v, K) for v in c] for c in proto]
            
            if f.type == Type.Until:
                # d') phi_K -> \bigvee_{L<=i<=K} sigma_i
                clause_list += [[-num(f,K)] + [num(f.r, i) for i in irange(L,K)]] # timesteps are fixed -> no add_timestep
                pass
            else:
                # d'') (\bigwedge_{L<=i<=K} delta_i) -> phi_K
                clause_list += [[num(f,K)] + [-num(f.l, i) for i in irange(L,K)]] # timesteps are fixed -> no add_timestep
                pass
            
        # 8) RELEASES
        elif f.type == Type.Release:
            # phi <-> delta R sigma
            # a) forall i: phi_i -> sigma_i
            # b) forall i: (phi_i && !phi_i+1) -> delta_i
            # c) forall i: (sigma_i && delta_i) -> phi_i
            # d) forall i: (phi_i+1 && sigma_i) -> phi_i
            #        a)                   b)                             c)                               d)
            proto = [
                     [-num(f), num(f.r)], 
                     [-num(f), num(f,+1), num(f.l)], 
                     [-num(f.r), -num(f.l), num(f)], 
                     [-num(f,+1), -num(f.r), num(f)]
                    ]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K-1) for c in proto]
            clause_list += [[add_timestep(v, K) for v in c] for c in proto]
            
            # e) (\bigwwedge_{L<=i<=K} sigma_i) -> phi_L
            clause_list += [[num(f,L)] + [-num(f.r, i) for i in irange(L,K)]] # timesteps are fixed -> no add_timestep
        
        elif f.type == Type.Identifier and self.instantiate_identifiers:
            proto = [[-num(f), num(f.value)], [num(f), -num(f.value)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K) for c in proto]
        
        for clause in clause_list:
            clause += fault_mode
        
#        print "Translating", f, "with fault mode", fault_mode, "result:"
#        print clause_list
        
        return clause_list

    def get_trace(self, result):
        """
        converts the result of a computation ("check" call can be used to compute or complete a trace) 
        into a ltlparser.ast.Node trace
        """
        t = Trace()
        t.k = self.trace_K
        t.l = self.trace_L
        vars = set().union(*self.var_nodes.values())
        sf = get_all_subformulas_list(self.formula, lambda n: n.type != Type.Identifier)
        for f in sorted(sf,key=lambda s: len(str(s))):
            t.signals.append(f)
            s = []
            for i in range(self.trace_len):
                s.append(True if (self.num(f,i) in result) else False)
            t.values.append(s)
#            if f in vars:
#                t.vars.append(len(t.signals)-1)
        for v in self.var_nodes:
            f = self.var_nodes[v][0]
            t.signals.append(f)
            t.vars.append(len(t.signals)-1)
            s = []
            for i in range(self.trace_len):
                s.append(True if (self.num(f,i) in result) else False)
            t.values.append(s)
        return t

    def create_fault_modes(self, f, **options):
        """
        this method defines the fault modes for a subformula f, depending on the given options 
        (e.g. ab_predicates implies that only a the healthy and faulty state are generated). 
        If variable_typos is enabled, all other variables are considered as fault modes for 
        an occurrence of a subformula. 
        The *_confusion modes use the other operators in the corresponding operator group as 
        fault modes, where for the binary temporal operators also a twisted operand order is
        considered.  
        """
        o = lambda k: options.get(k, False)
        
        if f.instmode != InstrumentationMode.Instrument or self.instrument_formula == False:
            self.fault_modes[f] = [f]
            return True
        
        if options.get('ab_predicates',False):
            self.fault_modes[f] = [f, True]
            return True
        
        all = options.get('all', False)
        bool_ops = [Type.BoolAnd, Type.BoolOr, Type.BoolXor, Type.Implies, Type.Equivalent]
        binary_temp_ops = [Type.Until, Type.WeakUntil, Type.Release]
        unary_temp_ops = [Type.Finally, Type.Globally, Type.Next]
        
        if f.type == Type.Identifier:
            self.fault_modes[f] = [f]
            if o('variable_typos') or all:
                for v in self.var_nodes:
                    if v != f.value:
                        self.fault_modes[f] += [Identifier(self.var_nodes[v][0].value, polarity=f.polarity).set_id(f.id)]
            pass
        else:
            self.fault_modes[f] = [f]
            if f.type in bool_ops and (o('bool_op_confusion') or all):
                pass
                for op in bool_ops:
                    if op != f.type:
                        self.fault_modes[f] += [Node(op, f.l, f.r, polarity=f.polarity).set_id(f.id)]
            
            elif f.type in binary_temp_ops and (o('binary_temp_op_confusion') or all):
                self.fault_modes[f] += [Node(f.type, f.r, f.l, polarity=f.polarity).set_id(f.id)]
                for op in binary_temp_ops:
                    if op != f.type:
                        self.fault_modes[f] += [Node(op, f.l, f.r, polarity=f.polarity).set_id(f.id), Node(op, f.r, f.l, polarity=f.polarity).set_id(f.id)]
                    
            elif f.type in unary_temp_ops and (o('unary_temp_op_confusion') or all):
                for op in unary_temp_ops:
                    if op != f.type:
                        self.fault_modes[f] += [Node(op, f.i, polarity=f.polarity).set_id(f.id)]

        if f in self.fault_modes:     
            while(len(self.fault_modes[f]) < 2**int(math.ceil(math.log(len(self.fault_modes[f]),2)))):
                self.fault_modes[f] += [False]
            
        return f in self.fault_modes and bool(self.fault_modes[f])

    # ========================================================================================================================
    # debug methods
    # ========================================================================================================================
    def print_variables(self):
        f_width = max(len("formula "),max(map(len,map(str,self.subformulae_nodes))))
        print 
        print "formula".ljust(f_width), 
        for i in range(self.trace_len):
            if i == self.trace_L:
                print "||", str(i).rjust(3),
            else: 
                print "|", str(i).rjust(3), 
        print
        print (f_width+sum(map(len,map(str,xrange(self.trace_len))))+5*self.trace_len+1) * "=",
        for f in self.subformulae_nodes:
            print
#            f = self.subformulae.get_key(f_num)
            print str(f).ljust(f_width),  
            for i in range(self.trace_len):
                if i == self.trace_L:
                    print "||", str(self.num(f,i)).rjust(3),
                else:
                    print "|", str(self.num(f,i)).rjust(3), 
        print
        for f in self.signals:
            print
#            f = self.subformulae.get_key(f_num)
            print str(f).ljust(f_width),  
            for i in range(self.trace_len):
                if i == self.trace_L:
                    print "||", str(self.num(f,i)).rjust(3),
                else:
                    print "|", str(self.num(f,i)).rjust(3), 
        print
        print
    
    def print_trace(self):
        f_width = max(len("formula "),max(map(len,map(str,self.subformulae_nodes))))
        print 
        print "formula".ljust(f_width), 
        for i in range(self.trace_len):
            if i == self.trace_L:
                print "||", str(i).rjust(3),
            else: 
                print "|", str(i).rjust(3), 
        print
        print (f_width+sum(map(len,map(str,xrange(self.trace_len))))+5*self.trace_len+1) * "=",
        for f in self.subformulae_nodes:
            print
#            f = self.subformulae.get_key(f_num)
            print str(f).ljust(f_width),  
            for i in range(self.trace_len):
                if i == self.trace_L:
                    print "||", str("X" if (self.num(f,i) in self.result[1]) else "_").rjust(3),
                else:
                    print "|", str("X" if (self.num(f,i) in self.result[1]) else "_").rjust(3), 
        print
        for f in self.signals:
            print
#            f = self.subformulae.get_key(f_num)
            print str(f).ljust(f_width),  
            for i in range(self.trace_len):
                if i == self.trace_L:
                    print "||", str("X" if (self.num(f,i) in self.result[1]) else "_").rjust(3),
                else:
                    print "|", str("X" if (self.num(f,i) in self.result[1]) else "_").rjust(3), 
        print
        print
        
    def print_sat_trace(self):
#        f_width = max(len("formula "),max(map(len,map(str,self.subformulae))))
        f_width = 4
        print 
        print (f_width+sum(map(len,map(str,xrange(self.trace_len))))+2*self.trace_len) * "=",
        
#        for f_num in sorted(self.subformulae.values()):
        for v in sorted(self.var_nodes.keys()):
            print
            f = self.subformulae.get_key(self.subformulae[self.var_nodes[v][0].id])
            print str(f).ljust(f_width),  
            for i in range(self.trace_len):
                if i == self.trace_L:
                    print " | ", 
                sys.stdout.write("X" if (self.num(f,i) in self.result[1]) else "_") 
        print
        print
        
    def print_unsat_core(self):
        for clause in self.result[1]:
            c = []
            for var_num in clause:
                var = (abs(var_num)-self.offset-1) % self.time_step_increase + 1
                timestep = int((abs(var_num)-self.offset-1) / self.time_step_increase)
                sign = "" if cmp(var_num,0) > 0 else "!"
                c += [sign + str(self.subformulae.get_key(var)) + "_t" + str(timestep)]
            print "["+",  ".join(c)+"]"



class DirectEncodingVar2(DirectEncoding):
    
    def __init__(self, formula, trace, exclude_traces=set(), **fault_mode_opts):
        super(DirectEncodingVar2, self).__init__(formula, trace, exclude_traces, **fault_mode_opts)
        self.formula.propagate_polarity()
    
    def clauses_for_formula(self, f, fault_mode = []):
        """
        This is the main method constructing the CNF clauses for a given formula f, adding the given fault_mode 
        to each clause at the end. 
        
        To understand the encoding rationale and how the clauses are constructed refer to the paper 
        "An LTL SAT Encoding for Behavioral Diagnosis" (Pill and Quaritsch, 2012) Tables 1 and 2. 
        """
        clause_list = []
        
        # read this as follows:    
        # f ... formula, l ... left sub-formula, r ... right sub-formula, "-" ... not
        # i ... inner part (unary operators), num(f, i) ... f_i (i time steps added)
        # e.g. if f <-> a && b, [-num(f), num(f.l), num(f.r)] is the clause (!f || a || b)  
        num = self.num
        add_timestep = self.add_timestep
        K = self.trace_K
        L = self.trace_L
        n = self.time_step_increase    # number to be added for each time-step increase
        
        # for all time-steps, if the prototype clause contains no variable from timestep +1
        # clauses for 0...K can be produced without overflow check  
        # if proto contains a +1, steps 0...K-1 can be created without overflow check, and last two clauses with
        # overflow check (thus using the add_timestep method)
        
        proto = []
        # 0) Constants
        if f.type == Type.Constant:
            if f.value == "True":
                clause_list += [[num(f,i)] for i in irange(0,K)]
            if f.value == "False":
                clause_list += [[-num(f,i)] for i in irange(0,K)]
        
        # 1) AND
        elif f.type == Type.BoolAnd:
            if f.polarity == True or f.polarity == None:
                proto += [[-num(f), num(f.l)], [-num(f), num(f.r)]]
            if f.polarity == False or f.polarity == None:
                proto += [[num(f), -num(f.l), -num(f.r)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K) for c in proto]
            
        # 2) OR    
        elif f.type == Type.BoolOr:
            if f.polarity == True or f.polarity == None:
                proto += [[-num(f), num(f.l), num(f.r)]]
            if f.polarity == False or f.polarity == None:
                proto += [[num(f), -num(f.l)], [num(f), -num(f.r)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K) for c in proto]
        
        # XOR
        elif f.type == Type.BoolXor:
            if f.polarity == True or f.polarity == None:
                proto += [[-num(f), -num(f.l), -num(f.r)], [-num(f), num(f.l), num(f.r)]]
            if f.polarity == False or f.polarity == None:
                proto += [[num(f), -num(f.l), num(f.r)], [num(f), num(f.l), -num(f.r)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K) for c in proto]
        
        # EQUIVALENT
        elif f.type == Type.Equivalent:
            if f.polarity == True or f.polarity == None:
                proto += [[-num(f), -num(f.l), num(f.r)], [-num(f), num(f.l), -num(f.r)]]
            if f.polarity == False or f.polarity == None:
                proto += [[num(f), -num(f.l), -num(f.r)], [num(f), num(f.l), num(f.r)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K) for c in proto]

        # IMPLICATION
        elif f.type == Type.Implies:
            if f.polarity == True or f.polarity == None:
                proto += [[-num(f), -num(f.l), num(f.r)]]
            if f.polarity == False or f.polarity == None:
                proto += [[num(f), num(f.l)], [num(f), -num(f.r)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K) for c in proto]
        
        # 3) NEXT
        elif f.type == Type.Next:
            if f.polarity == True or f.polarity == None:
                proto += [[-num(f), num(f.i,+1)]]
            if f.polarity == False or f.polarity == None:
                proto += [[num(f), -num(f.i,+1)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K-1) for c in proto]
            clause_list += [[add_timestep(v, K) for v in c] for c in proto]
        
        # 4) NOT
        elif f.type == Type.BoolNot:
            if f.polarity == True or f.polarity == None:
                proto += [[-num(f), -num(f.i)]]
            if f.polarity == False or f.polarity == None:
                proto += [[num(f), num(f.i)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K) for c in proto]
        
        # 5) FINALLY    
        elif f.type == Type.Finally:
            # phi <-> F(delta_i)
            # a) and
            # b)
            # forall i: phi_i+1 -> phi_i (incl. phi_L -> phi_K)
            if f.polarity == False or f.polarity == None:
                proto = [[-num(f,+1), num(f)], [-num(f.i), num(f)]]
                clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K-1) for c in proto]
                clause_list += [[add_timestep(v, K) for v in c] for c in proto]
            
            # d) phi_L -> \bigvee_(L<=i<=K): (delta_i)
            clause_list += [[-num(f,L)] + [num(f.i, i) for i in irange(L,K)]]   # timesteps are fixed -> no add_timestep
            
            if f.polarity == True or f.polarity == None:
                # e) forall 0<=i<=K: phi_i -> (delta_i or phi_i+1)
                proto = [[-num(f), num(f.i), num(f,+1)]]
#                clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, L-1) for c in proto]
                clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K-1) for c in proto]
                clause_list += [[add_timestep(v, K) for v in c] for c in proto]
            
        # 6) GLOBALLY
        elif f.type == Type.Globally:
            # phi <-> G(delta_i)
            # a) - c)
            # phi_i -> delta_i, phi_i -> phi_i+1, !phi_i -> (!delta_i | !phi_i+1)
            proto = []
            if f.polarity == True or f.polarity == None:
                proto += [
                            [-num(f), num(f.i)],               # a)
                            [-num(f), num(f,+1)],              # b)
                         ]
            if f.polarity == False or f.polarity == None:
                proto += [
                            [num(f), -num(f.i), -num(f,+1)]    # c)
                         ]
            
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K-1) for c in proto]
            clause_list += [[add_timestep(v, K) for v in c] for c in proto]

            # f) !phi_K -> \bigvee_(L<=i<=K) !delta_i   
            clause_list += [[num(f,K)] + [-num(f.i, i) for i in irange(L,K)]] # timesteps are fixed -> no add_timestep
                        
        # 7) UNTIL and WEAKUNTIL
        elif f.type == Type.Until or f.type == Type.WeakUntil:
            # phi <-> delta U sigma
            # a) forall i: phi_i -> (sigma_i || (delta_i && phi_i+1)) (expansion rule)
            # b) forall i: sigma_i -> phi_i
            # c) forall i: (delta_i && phi_i+1) -> phi_i
            #        a)     
            if f.polarity == True or f.polarity == None:
                proto += [[-num(f), num(f.r), num(f.l)], [-num(f), num(f.r), num(f,+1)]]
            if f.polarity == False or f.polarity == None:
                proto += [[-num(f.r), num(f)], [-num(f.l), -num(f,+1), num(f)]]
                
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K-1) for c in proto]
            clause_list += [[add_timestep(v, K) for v in c] for c in proto]
            
            if f.type == Type.Until:
                # d') phi_K -> \bigvee_{L<=i<=K} sigma_i
                clause_list += [[-num(f,K)] + [num(f.r, i) for i in irange(L,K)]] # timesteps are fixed -> no add_timestep
                pass
            else:
                # d'') (\bigwedge_{L<=i<=K} delta_i) -> phi_K
                clause_list += [[num(f,K)] + [-num(f.l, i) for i in irange(L,K)]] # timesteps are fixed -> no add_timestep
                pass
            
        # 8) RELEASES
        elif f.type == Type.Release:
            # phi <-> delta R sigma
            # a) forall i: phi_i -> sigma_i
            # b) forall i: (phi_i && !phi_i+1) -> delta_i
            # c) forall i: (sigma_i && delta_i) -> phi_i
            # d) forall i: (phi_i+1 && sigma_i) -> phi_i
            #        a)                   b)                             c)                               d)
            if f.polarity == True or f.polarity == None:
                proto += [[-num(f), num(f.r)], [-num(f), num(f,+1), num(f.l)]]
            if f.polarity == False or f.polarity == None:
                proto += [[-num(f.r), -num(f.l), num(f)], [-num(f,+1), -num(f.r), num(f)]]
            
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K-1) for c in proto]
            clause_list += [[add_timestep(v, K) for v in c] for c in proto]
            
            # e) (\bigwwedge_{L<=i<=K} sigma_i) -> phi_L
            clause_list += [[num(f,L)] + [-num(f.r, i) for i in irange(L,K)]] # timesteps are fixed -> no add_timestep
        
        elif f.type == Type.Identifier and self.instantiate_identifiers:
            proto = [[-num(f), num(f.value)], [num(f), -num(f.value)]]
            clause_list += [[cmp(v,0)*(abs(v)+n*i) for v in c] for i in irange(0, K) for c in proto]
        
        for clause in clause_list:
            clause += fault_mode
        
#        print "Translating", f, "with fault mode", fault_mode, "result:"
#        print clause_list
        
        return clause_list
