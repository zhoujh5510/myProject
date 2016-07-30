from ab_constraint import AbConstraint
from gate import Gate
from gate_with_ab_predicate import GateWithAbPredicate, GateSentence
from sentences import PushSentence, PopSentence, BlockingSentence
from collections import OrderedDict
from pymbd.sat.description import Description
from pymbd.sat.problem import Problem
from pymbd.sat.variable import Variable
import random

def prefix(var):
    return 'x' + var

def ab_pred(var):
    return 'AB' + var
        
def prefix_gate(gate):
    output = prefix(gate.output)
    inputs = []
    for input in gate.inputs:
        inputs.append(prefix(input))
    return Gate(output, gate.type, inputs)


class Net(object):
    
    def __init__(self, inputs, outputs, gates, **options):
        self.inputs = OrderedDict((i, None) for i in inputs)
        self.outputs = OrderedDict((o, None) for o in outputs)
        self.gates = OrderedDict((g.output, g) for g in gates)
        self.sat_engine_name = options.get('sat_solver', None)
        self.check_problem = Problem(self.sat_engine_name)
        self.comp_problem = self.check_problem
        self.check_queries = 0
        self.comp_queries = 0
        self.queries = 0
        self.options = options
        options['relaunch_sat_solver'] = options.get('relaunch_sat_solver', False)
        # HACK follows!!
        if self.sat_engine_name != "yices" and self.sat_engine_name != None and self.sat_engine_name != "scryptominisat" and self.sat_engine_name != "scryptominisat-async" and self.sat_engine_name != "scryptominisat-async-mod" and self.sat_engine_name != "yices-cn-dimacs" and self.sat_engine_name != "yices-maxsat-dimacs" and self.sat_engine_name != "yices-cn-cnf":
            options['relaunch_sat_solver'] = True
        options['reuse_sat'] = options.get('reuse_sat', False)
        options['separate_tp'] = options.get('separate_tp', False)
        self.first_check_call = True
        self.first_comp_call = True
        self.previous_diagnoses = set()
        self.last_max_card = 0
    
    def set_options(self, **options):
        self.options.update(options)
    
    def generate_random_inputs(self):
        for i in self.inputs:
            self.inputs[i] = random.uniform(0,1) > 0.5
            
    def reset_outputs(self):
        for i in self.outputs:
            self.outputs[i] = None
            
    def mutate_net(self, gates):
        """
        replaces the gates in the net with those given in `gates' (gates are identified 
        by their output name), and returns the original gates
        """
        orig_gates = []
        for g in gates:
            if g.output in self.gates:
                orig_gates.append(self.gates[g.output])
                self.gates[g.output] = g
        return orig_gates
            
    def calculate_outputs(self):
        """
        calculate the output of the net using the current input values (e.g. generated 
        using generate_random_inputs above) and output values. Note that for generating 
        the SatProblem, all variables are prefixed (using 'x'), because valid identifiers 
        must start with a letter (and some ISCAS files use names like 11gat).
        The abnormal predicate of every gate is named AB<gate>, e.g. ABx11gat.
        """ 
        
        vars = []
        for input,value in self.inputs.iteritems():
            vars.append(Variable(prefix(input), Variable.BOOLEAN, value)) 

        for output,value in self.outputs.iteritems():
            vars.append(Variable(prefix(output), Variable.BOOLEAN, value))

        for gate in set(self.gates.keys())-set(self.outputs.keys()):
            vars.append(Variable(prefix(gate), Variable.BOOLEAN, None))
                    
        sentences = []
        for output, gate in self.gates.iteritems():
            sentences.append(GateSentence(prefix_gate(gate)))
        
        p = Problem(self.sat_engine_name)
        result = p.solve(Description(vars, sentences))
        outputs = result.get_values()
        p.finished()
        
        for output,value in outputs.iteritems():
            if output[1:] in self.outputs: # just set outputs, no internal lines!
                self.outputs[output[1:]] = value 

        return result.sat()

    def construct_problem_for_reuse(self):
    
        vars = []
        sentences = []
        
        # primary input variables are constrained to their value
        for input,value in self.inputs.iteritems():
            vars.append(Variable(prefix(input), Variable.BOOLEAN, value))  

        # primary output variables are constrained to their value
        for output,value in self.outputs.iteritems():
            vars.append(Variable(prefix(output), Variable.BOOLEAN, value))
        
        # all other output variables (internal lines) are unconstrained
        for gate in set(self.gates.keys())-set(self.outputs.keys()):
            vars.append(Variable(prefix(gate), Variable.BOOLEAN, None))
        
        # create a variable for the AB predicate of each gate:
        for gate in set(self.gates.keys()):
            vars.append(Variable(ab_pred(prefix(gate)), Variable.BOOLEAN, None))
        
        # all gates are equipped with (not ABx => (= x ...))
        for gate in set(self.gates.keys()):
            sentences.append(GateWithAbPredicate(ab_pred(prefix(gate)), prefix_gate(self.gates[gate])))
        
        return vars, sentences


    def check_consistency(self, h):
        """
        Calculate a conflict set by constraining the AB predicates depending 
        on a gates inclusion in h. These new sentences are added to the problem 
        and the SAT solver is started again. If it returns SAT, the hitting set 
        h is consistent, otherwise it returns UNSAT.
        """
        if self.options['separate_tp'] == True:
            self.check_queries += 1
            if self.check_queries > 100 or self.options['relaunch_sat_solver']:
                self.check_queries = 0
                self.check_problem.finished()
                self.check_problem = Problem(self.sat_engine_name)
                self.first_check_call = True
        else:
            self.queries += 1
            if self.queries > 100 or self.options['relaunch_sat_solver']:
                self.queries = 0
                self.check_problem.finished()
                self.check_problem = Problem(self.sat_engine_name)
                self.comp_problem = self.check_problem
                self.first_check_call = True
                self.first_comp_call = True
        
        if self.options['reuse_sat']:
            
            if self.first_check_call:
                self.first_check_call = False
                
                if self.options['separate_tp'] == True and self.check_problem == self.comp_problem:
                    self.check_problem = Problem(self.sat_engine_name)
                                
                vars, sentences = self.construct_problem_for_reuse()
                
                sentences.append(PushSentence())
                
                # for all gates not in h set the AB predicate to false.
                for gate in set(self.gates.keys())-h:
                    sentences.append(AbConstraint(prefix(gate), False, extended=False))

                for gate in h:
                    sentences.append(AbConstraint(prefix(gate), True, extended=False))
        
                # is this problem satisfiable?
                r = self.check_problem.solve(Description(vars, sentences), calculate_unsat_core=False)
                
                return r.sat()
                
            else: # (not self.first_check_consistency)
                
                sentences = []
                
                sentences.append(PopSentence())
                sentences.append(PushSentence())

                # for all gates not in h set the AB predicate to false.
                for gate in set(self.gates.keys())-h:
                    sentences.append(AbConstraint(prefix(gate), False, extended=False))

                for gate in h:
                    sentences.append(AbConstraint(prefix(gate), True, extended=False))
        
                # is this problem satisfiable?
                r = self.check_problem.solve_again(sentences, calculate_unsat_core=False)
                
                return r.sat()

    
        else: # (not self.reuse_sat)
            
            if self.options['separate_tp'] == True and self.check_problem == self.comp_problem:
                self.check_problem = Problem(self.sat_engine_name)
            
            vars = []
            sentences = []
            
            # primary input variables are constrained to their value
            for input,value in self.inputs.iteritems():
                vars.append(Variable(prefix(input), Variable.BOOLEAN, value))  
    
            # primary output variables are constrained to their value
            for output,value in self.outputs.iteritems():
                vars.append(Variable(prefix(output), Variable.BOOLEAN, value))
            
            # all other output variables (internal lines) are unconstrained
            for gate in set(self.gates.keys())-set(self.outputs.keys()):
                vars.append(Variable(prefix(gate), Variable.BOOLEAN, None))
            
            # all gate outputs except those in `h' behave according to their gate function
            for gate in set(self.gates.keys())-h:
                sentences.append(GateSentence(prefix_gate(self.gates[gate])))
    
            # is this problem satisfiable?
            r = self.check_problem.solve(Description(vars, sentences), calculate_unsat_core=False)
            
            return r.sat()
            
    def calculate_conflicts(self, h):
        """
        Calculate a conflict set by constraining the AB predicates depending 
        on a gates inclusion in h. These new sentences are added to the problem 
        and the SAT solver is started again. This should return a new UNSAT 
        core, which is returned as new conflict set. 
        """
        if self.options['separate_tp'] == True:
            self.comp_queries += 1
            if self.comp_queries > 100 or self.options['relaunch_sat_solver']:
                self.comp_queries = 0
                self.comp_problem.finished()
                self.comp_problem = Problem(self.sat_engine_name)
                self.first_comp_call = True
        else:
            self.queries += 1
            if self.queries > 100 or self.options['relaunch_sat_solver']:
                self.queries = 0
                self.check_problem.finished()
                self.check_problem = Problem(self.sat_engine_name)
                self.comp_problem = self.check_problem
                self.first_check_call = True
                self.first_comp_call = True
        
        if self.options['reuse_sat']:
            
            if self.first_comp_call:
                self.first_comp_call = False
                
                vars, sentences = self.construct_problem_for_reuse()
                
                sentences.append(PushSentence())
                
                # for all gates not in h set the AB predicate to false.
                for gate in set(self.gates.keys())-h:
                    sentences.append(AbConstraint(prefix(gate), False))

                for gate in h:
                    sentences.append(AbConstraint(prefix(gate), True))
        
                # get me an unsatisfiable core of AB predicates
                r = self.comp_problem.solve(Description(vars, sentences), calculate_unsat_core=True)
                
                if (r.sat()):
                    return None
                else:
                    conflict = map(lambda x: x[1:], r.get_unsat_core())
                    return frozenset(conflict)
                
            else: # not self.first_calculate_conflicts:
                sentences = []
                
                sentences.append(PopSentence())
                sentences.append(PushSentence())
               
                # for all gates not in h set the AB predicate to false.
                for gate in set(self.gates.keys())-h:
                    sentences.append(AbConstraint(prefix(gate), False))

                for gate in h:
                    sentences.append(AbConstraint(prefix(gate), True)) 
                    
                r = self.comp_problem.solve_again(sentences, calculate_unsat_core=True)
                
                if (r.sat()):
                    return None
                else:
                    conflict = map(lambda x: x[1:], r.get_unsat_core())
                    return frozenset(conflict)
        
        else: # (not self.reuse_sat)
                   
            vars = []
            sentences = []
            
            # primary input variables are constrained to their value
            for input, value in self.inputs.iteritems():
                vars.append(Variable(prefix(input), Variable.BOOLEAN, value))  
    
            # primary output variables are constrained to their value
            for output, value in self.outputs.iteritems():
                vars.append(Variable(prefix(output), Variable.BOOLEAN, value))
    
            # all other output variables (internal lines) are unconstrained
            for gate in set(self.gates.keys())-set(self.outputs.keys()):
                vars.append(Variable(prefix(gate), Variable.BOOLEAN, None))
    
            # create a variable for the AB predicate of each gate except those in `h':
            for gate in set(self.gates.keys())-h:
                vars.append(Variable(ab_pred(prefix(gate)), Variable.BOOLEAN, None))
            
            # all gates except those in `h' are equipped with (not ABx => (= x ...))
            for gate in set(self.gates.keys())-h:
                sentences.append(GateWithAbPredicate(ab_pred(prefix(gate)), prefix_gate(self.gates[gate])))
            
            sentences.append(PushSentence())
            
            # for all gates not in h set the AB predicate to false.
            for gate in set(self.gates.keys())-h:
                sentences.append(AbConstraint(prefix(gate), False))
    
            # get me an unsatisfiable core of AB predicates
            r = self.comp_problem.solve(Description(vars, sentences), calculate_unsat_core=True)
            
            if (r.sat()):
                return None
            else:
                conflict = map(lambda x: x[1:], r.get_unsat_core())
                return frozenset(conflict)
            
    def calculate_next_diagnosis(self, blocked_diagnoses, max_card=None, find_all_sols=False):
        """
        
        """
        
        if self.queries > 100 or self.options['relaunch_sat_solver'] or (self.sat_engine_name == "yices-cn-cnf" and self.last_max_card != max_card):
            self.queries = 0
            self.check_problem.finished()
            self.check_problem = Problem(self.sat_engine_name)
            self.comp_problem = self.check_problem
            self.first_check_call = True
            self.first_comp_call = True
            blocked_diagnoses = set(blocked_diagnoses) | self.previous_diagnoses
        
        self.last_max_card = max_card
        
        if self.options['reuse_sat']:
            
            self.ab_vars = []
            if self.first_comp_call:
                self.first_comp_call = False
                
                vars, sentences = self.construct_problem_for_reuse()
                
                # for all gates not in h set the AB predicate to false.
                for gate in set(self.gates.keys()):
                    sentences.append(AbConstraint(prefix(gate), False, weight=1))
                    self.ab_vars.append("AB"+prefix(gate))
                
                for diag in blocked_diagnoses:
                    sentences.append(BlockingSentence(diag))
        
                # get me an unsatisfiable core of AB predicates
                r = self.comp_problem.solve(Description(vars, sentences), calculate_unsat_core=True, max_card=max_card, find_all_sols=find_all_sols, ab_vars=self.ab_vars)
                
                if r:
                    self.previous_diagnoses |= frozenset(r)
                return r
                
            else: # not self.first_calculate_conflicts:
                sentences = []
                           
                for diag in blocked_diagnoses:
                    sentences.append(BlockingSentence(diag))

                r = self.comp_problem.solve_again(sentences, calculate_unsat_core=True, max_card=max_card, find_all_sols=find_all_sols, ab_vars=self.ab_vars)
                
                if r:
                    self.previous_diagnoses |= frozenset(r)
                return r
        
        else: # (not self.reuse_sat)
                   
            vars = []
            sentences = []
            ab_vars = []
            
            # primary input variables are constrained to their value
            for input, value in self.inputs.iteritems():
                vars.append(Variable(prefix(input), Variable.BOOLEAN, value))  
    
            # primary output variables are constrained to their value
            for output, value in self.outputs.iteritems():
                vars.append(Variable(prefix(output), Variable.BOOLEAN, value))
    
            # all other output variables (internal lines) are unconstrained
            for gate in set(self.gates.keys())-set(self.outputs.keys()):
                vars.append(Variable(prefix(gate), Variable.BOOLEAN, None))
    
            # create a variable for the AB predicate of each gate except those in `h':
            for gate in set(self.gates.keys()):
                vars.append(Variable(ab_pred(prefix(gate)), Variable.BOOLEAN, None))
            
            # all gates except those in `h' are equipped with (not ABx => (= x ...))
            for gate in set(self.gates.keys()):
                sentences.append(GateWithAbPredicate(ab_pred(prefix(gate)), prefix_gate(self.gates[gate])))
            
            # for all gates not in h set the AB predicate to false.
            for gate in set(self.gates.keys()):
                sentences.append(AbConstraint(prefix(gate), False, weight=1))
                ab_vars.append("AB"+prefix(gate))
    
            for diag in blocked_diagnoses:
                sentences.append(BlockingSentence(diag))
    
            # get me an unsatisfiable core of AB predicates
            r = self.comp_problem.solve(Description(vars, sentences), calculate_unsat_core=True, ab_vars=ab_vars, max_card=max_card, find_all_sols=find_all_sols)
            
            if r:
                self.previous_diagnoses |= frozenset(r)
            return r

    def input_values_compact(self):
        return map(lambda v: v and 1 or 0, self.inputs.values())

    def output_values_compact(self):
        return map(lambda v: v and 1 or 0, self.outputs.values())

    def finished(self):
        if self.check_problem:
            self.check_problem.finished()
        if self.comp_problem and self.check_problem != self.comp_problem:
            self.comp_problem.finished()
    
