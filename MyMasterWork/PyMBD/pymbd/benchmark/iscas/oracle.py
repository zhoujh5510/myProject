from net import Net
from parser import SimpleParser
from pymbd.diagnosis.description import Description
from pymbd.util.two_way_dict import TwoWayDict
import time

class IscasOracle(Description):
    
    def __init__(self, sisc_file, inputs, outputs, **options):
        super(IscasOracle, self).__init__([], **options)
        self.sisc_file = sisc_file
        self.comp_calls = 0
        self.check_calls = 0
        self.comp_time = 0
        self.check_time = 0
        self.scs = set()
        self.setup = False
        self.inputs = inputs
        self.outputs = outputs
        self.net = None
        
    def setup_net(self):
        if not self.setup:
            self.setup = True
            self.net = Net(*SimpleParser(open(self.sisc_file)).parse(), **self.options)
            for c,i in enumerate(self.net.inputs):
                self.net.inputs[i] = self.inputs[c] == 1
            for c,i in enumerate(self.net.outputs):
                self.net.outputs[i] = self.outputs[c] == 1
            self.components = TwoWayDict(dict(enumerate(self.net.gates.keys())))
            
    def set_options(self, **options):
        super(IscasOracle, self).set_options(**options)
        if self.net is not None:
            self.net.set_options(**options)
    
    def get_num_components(self):
        self.setup_net()
        return len(self.components)
        
    def get_conflict_set(self, h):
        self.setup_net()
        self.comp_calls += 1
        t0 = time.time()
        cs = self.net.calculate_conflicts(self.numbers_to_gates(h))
        t1 = time.time()
        self.comp_time += t1-t0
        if cs:
            self.scs.add(frozenset(cs))
            return self.gates_to_numbers(cs)
        else:
            return None
    
    def check_consistency(self, h):
        self.setup_net()
        self.check_calls += 1
        t0 = time.time()
        sat = self.net.check_consistency(self.numbers_to_gates(h))
        t1 = time.time()
        self.check_time += t1-t0
        return sat

    def get_next_diagnosis(self, previous_diagnoses, max_card=None):
        self.setup_net()
        self.comp_calls += 1
        t0 = time.time()
#        print "get_next_diagnosis(%s,%d)"%(previous_diagnoses, max_card)
        diag = self.net.calculate_next_diagnosis(map(self.numbers_to_gates,previous_diagnoses), max_card=max_card)
#        print "solution:", diag
        t1 = time.time()
        self.comp_time += t1-t0
        if diag:
            return self.gates_to_numbers(diag)
        else:
            return None
        
    def get_all_diagnoses(self, previous_diagnoses, max_card=None, max_solutions=None):
        self.setup_net()
        self.comp_calls += 1
        t0 = time.time()
        diag = self.net.calculate_next_diagnosis(map(self.numbers_to_gates,previous_diagnoses), max_card=max_card, find_all_sols=True)
        t1 = time.time()
        self.comp_time += t1-t0
        if diag:
            return map(self.gates_to_numbers, diag)
        else:
            return None
        

    def finished(self):
        self.net.finished()
        
    def gates_to_numbers(self, gates):
        return frozenset(map(lambda g: self.components.key(g), gates))
        
    def numbers_to_gates(self, numbers):
        return frozenset(map(lambda n: self.components[n], numbers))
        
        
class IscasOracleOld(IscasOracle):

    def __init__(self, sisc_file, inputs, mutated_gates, **options):
        super(IscasOracleOld, self).__init__(None, [], [], **options)
        self.sisc_file = sisc_file
        self.mutated_gates = mutated_gates
        self.net = Net(*SimpleParser(open(sisc_file)).parse(), **options)
        for c,i in enumerate(self.net.inputs):
            self.net.inputs[i] = inputs[c] == 1
        orig_gates = self.net.mutate_net(mutated_gates)
        self.net.calculate_outputs()
        self.net.mutate_net(orig_gates)
        self.comp_calls = 0
        self.check_calls = 0
        self.comp_time = 0
        self.check_time = 0
        self.scs = set()
        self.components = TwoWayDict(dict(enumerate(self.net.gates.keys())))
        
    def setup_net(self):
        pass
        
