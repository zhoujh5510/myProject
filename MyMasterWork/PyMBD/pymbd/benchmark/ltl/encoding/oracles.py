from collections import defaultdict
from ..ltlparser.ast import get_all_subformulas, Type, get_all_subformulas_list, \
    Node
from direct_encoding import DirectEncoding, DirectEncodingVar2
from pymbd.util.two_way_dict import TwoWayDict
from pymbd.diagnosis.description import Description
import time


class FmConflictSet(object):
    """
    This encapsulates a conflict set with fault modes for the HS-DAG algorithm. In order to speed up the algorithm, 
    the conflict set is divided into two sets, the ``top'' one, containing all (component,mode) tuples where the 
    mode is NORMAL/HEALTHY, and the ``bot'' one containing all the others. For a more detailed description of the 
    algorithm see hittingset.algorithm.greiner.GreinerFaultModes class. 
    """
    __slots__ = ['top', 'bot']
    
    def __init__(self, top, bot):
        self.top, self.bot = top, bot

    def __iter__(self):
        for e in self.top:
            yield e
        for e in self.bot:
            yield e
    
    def __lt__(self, other):
        return (self.top | self.bot) < (other.top | other.bot)
    def __gt__(self, other):
        return (self.top | self.bot) > (other.top | other.bot)
    def __le__(self, other):
        return (self.top | self.bot) <= (other.top | other.bot)
    def __ge__(self, other):
        return (self.top | self.bot) >= (other.top | other.bot)
    def __and__(self, other):
        return FmConflictSet(self.top & other.top, self.bot & other.bot)
    def __or__(self, other):
        return FmConflictSet(self.top | other.top, self.bot | other.bot)
    def __len__(self):
        return len(self.top) + len(self.bot)
    def __repr__(self):
        return "FmConflictSet(%s,%s)" % (self.top, self.bot)

class SimpleHittingSetDescription(Description):
    """
    An oracle/description object for a non-fault-mode based computation (i.e. only binary health variables). 
    In this case, the conflict sets are translated to sets of integer numbers, where each number represents 
    a subformula. This is to make the diagnosis algorithm easier to debug and avoids all problems that might 
    arise from using (complex) node objects inside the hitting set algorithms. The mapping from and to those 
    integers is done in the numbers_to_nodes and nodes_to_numbers methods, respectively, for each call 
    of check_consistency and get_conflict_set. By using the two-way dictionary, this should not impose any 
    performance problems. 
    """
    def __init__(self, specification, trace, **options):
        super(SimpleHittingSetDescription, self).__init__([], **options)
        self.spec = specification
        self.trace = trace
        enc_options = {'ab_predicates':True}
        if options.get('variable_typos',False) is True:
            enc_options['variable_typos'] = True
        self.variant = options.get('encoding_variant_class', 'DirectEncoding')
        self.de = eval(self.variant)(self.spec, self.trace, **enc_options)
        self.components = TwoWayDict(dict(enumerate(get_all_subformulas(self.spec, Type.ANY))))
        self.scs = []
    
    def get_first_conflict_set(self):
        return self.get_conflict_set(set())
    
    def check_consistency(self, h):
#        print "check_consistency, h=%s" % map(lambda n: "n"+str(n.id), self.numbers_to_nodes(h))
        t0 = time.time()
        self.check_calls += 1
        r = self.de.check(abnormal_subformulae=self.numbers_to_nodes(h), sat_solver=self.options.get('sat_solver', 'picosat'), config=self.options.get('config',{}))
        t1 = time.time()
        self.check_time += t1-t0
#        print "->", r
        return r

    def get_conflict_set(self, h):
#        print "get_conflict_set, h=%s" % map(lambda n: "n"+str(n.id), self.numbers_to_nodes(h))
        t0 = time.time()
        self.comp_calls += 1
        r, cs = self.de.get_conflict(abnormal_subformulae=self.numbers_to_nodes(h), sat_solver=self.options.get('sat_solver', 'picosat'), config=self.options.get('config',{}))
        if r:
            return None
        else:
#            print cs
            if not self.de.check(abnormal_subformulae=cs, sat_solver=self.options.get('sat_solver', 'picosat'), config=self.options.get('config',{})):
                print("WARNING! Result is inconsistent, i.e. not a real conflict set!")
            
            t1 = time.time()
            self.comp_time += t1-t0
            self.scs.append(frozenset(cs))
#            print "->", map(lambda n: "n"+str(n.id), cs)
            return self.nodes_to_numbers(cs)
        
    def get_next_diagnosis(self, previous_diagnoses, max_card=None):
        self.comp_calls += 1
        t0 = time.time()
#        print "get_next_diagnosis(%s,%d)"%(previous_diagnoses, max_card)
        diag = self.de.calculate_next_diagnosis(map(self.numbers_to_nodes,previous_diagnoses), max_card=max_card, sat_solver=self.options.get('sat_solver', 'simple-yices'), config=self.options.get('config',{}))
#        print "solution:", diag
        t1 = time.time()
        self.comp_time += t1-t0
        if diag:
            return self.nodes_to_numbers(diag)
        else:
            return None
        
    def get_all_diagnoses(self, previous_diagnoses, max_card=None, max_solutions=None):
        self.comp_calls += 1
        t0 = time.time()
        diag = self.de.calculate_next_diagnosis(map(self.numbers_to_nodes,previous_diagnoses), max_card=max_card, find_all_sols=True, sat_solver=self.options.get('sat_solver', 'simple-yices'), config=self.options.get('config',{}))
        t1 = time.time()
        self.comp_time += t1-t0
        if diag:
            return map(self.nodes_to_numbers, diag)
        else:
            return None
    
    def nodes_to_numbers(self, gates):
        return frozenset(map(lambda g: self.components.key(g), gates))
        
    def numbers_to_nodes(self, numbers):
        return frozenset(map(lambda n: self.components[n], numbers))
    
    
class TraceDiagnosisHittingSetDescription(Description):
    """
    Used for the case when the formula is assumed to be correct and the diagnosis process acts 
    on the trace. In this case, the conflict sets are made up from tuples (signal,time step). 
    Since tuples of strings and integers are okay for the hitting set algorithms, no further 
    mapping is necessary. 
    """
    def __init__(self, specification, trace, **options):
        super(TraceDiagnosisHittingSetDescription, self).__init__([], **options)
        self.spec = specification
        self.trace = trace
        self.variant = options.get('encoding_variant_class', 'DirectEncoding')
        self.de = eval(self.variant)(self.spec, self.trace, instrument_trace=True)
    
    def get_first_conflict_set(self):
        return self.get_conflict_set(set())
    
    def check_consistency(self, h):
#        print "check_consistency, h=%s" % h
        t0 = time.time()
        self.check_calls += 1
        r = self.de.check(abnormal_trace_points=h)
        t1 = time.time()
        self.check_time += t1-t0
        return r

    def get_conflict_set(self, h):
        t0 = time.time()
        self.comp_calls += 1
        r, cs = self.de.get_conflict(abnormal_trace_points=h)
        if r:
            return None
        else:            
            t1 = time.time()
            self.comp_time += t1-t0
            return frozenset(cs)


class FaultModeHittingSetDescription(Description):
    """
    Oracle/Description used for fault mode diagnosis runs. Again the subformulae are mapped to integer 
    numbers, which together with the fault mode number form tuples for the conflict sets (component,faultmode).
    A conflict set is sometimes called mode assignment in this class (i.e. a mode combination that leads to a 
    conflict).  
    """
    def __init__(self, specification, trace, **options):
        super(FaultModeHittingSetDescription, self).__init__([], **options)
        self.spec = specification
        self.trace = trace
        self.variant = options.get('encoding_variant_class', 'DirectEncoding')
        self.de = eval(self.variant)(self.spec, self.trace, **options.get('fault_mode_opts', {'all':True}))
        self.components = TwoWayDict(dict(enumerate(get_all_subformulas_list(self.spec, Type.ANY))))
        self.fault_modes = None
        self.scs = set()
        self.sat_solver = options.get('sat_solver', 'picosat')
    
    def get_first_conflict_set(self):
#        self.check_calls += 1
        return self.get_conflict_set(set())
    
    def check_consistency(self, h):
#        print "check_consistency, h=%s" % h
#        for k,v in self.tuples_to_mode_assignment(h).iteritems():
#            print k, v, self.de.fault_modes[k][v]
        self.check_calls += 1
        tuples = self.tuples_to_mode_assignment(h)
        t0 = time.time()
        r = self.de.check_with_modes(mode_assignment=tuples,sat_solver=self.sat_solver)
        t1 = time.time()
        self.check_time += t1-t0
        return r

    def get_fault_modes_for(self, component):
        """
        In the diagnosis algorithm (HS-DAG), this method is used to determine which fault 
        modes should be used to expand a node, e.g. if component 3 has fault modes 0,1,2,False
        (False meaning deactivated), then this method would return 1,2. The result of this 
        computation is cached such that it can be used for the next query again. 
        """
        if not self.fault_modes:
            self.fault_modes = defaultdict(list)
            for num,sf in self.components.iteritems():
                if sf in self.de.fault_modes:
                    for i,fm in enumerate(self.de.fault_modes[sf]):
                        if fm != False and fm != sf:
                            self.fault_modes[num].append((num,i))
#            print sum(map(len,self.fault_modes.values()))
#            print self.components
        return self.fault_modes[component]

    def get_conflict_set(self, h):
#        print "get_conflict_set, h=%s" % h
        t0 = time.time()
        self.comp_calls += 1
        r, cs = self.de.get_conflict_with_modes(mode_assignment=self.tuples_to_mode_assignment(h), sat_solver=self.sat_solver)
        if r:
            return None
        else:
#            if not self.de.check_with_modes(mode_assignment=cs):
#                print("WARNING! Result is inconsistent, i.e. not a real conflict set!")
            
            t1 = time.time()
            self.comp_time += t1-t0
#            print map(str, cs)
#            print "--> CS:", self.nodes_to_tuples(cs)
#            print
            result = self.nodes_to_tuples(cs) # - self.nodes_to_tuples(self.tuples_to_nodes(h))
            self.scs.add(frozenset(result)) 
            return result

    def get_next_diagnosis(self, previous_diagnoses, max_card=None):
        self.comp_calls += 1
        t0 = time.time()
#        print "get_next_diagnosis(%s,%d)"%(previous_diagnoses, max_card)
        diag = self.de.calculate_next_diagnosis(map(self.tuples_to_mode_assignment,previous_diagnoses), max_card=max_card, sat_solver=self.options.get('sat_solver', 'simple-yices'))
#        print "solution:", diag
        t1 = time.time()
        self.comp_time += t1-t0
        if diag:
            return self.nodes_to_tuples(diag)
        else:
            return None
        
    def get_all_diagnoses(self, previous_diagnoses, max_card=None, max_solutions=None):
        self.comp_calls += 1
        t0 = time.time()
        diag = self.de.calculate_next_diagnosis(map(self.tuples_to_mode_assignment,previous_diagnoses), max_card=max_card, find_all_sols=True, sat_solver=self.options.get('sat_solver', 'simple-yices'))
        t1 = time.time()
        self.comp_time += t1-t0
        if diag:
            return map(self.nodes_to_tuples, diag)
        else:
            return None

    def tuples_to_mode_assignment(self, tuples):
        return dict((self.components[t[0]],t[1]) for t in tuples)
    
    def nodes_to_tuples(self, nodes):
        result = set()
        for n,m in nodes:
            result.add((self.components.key(n), m))
#        for n in nodes:
#            for f in xrange(1,len(self.de.fault_modes[n])):
#                if self.de.fault_modes[n][f] != False:
#                    result.add((self.components.key(n),f))
        return frozenset(result)
        
#    def tuples_to_nodes(self, tuples):
#        return frozenset(map(lambda n: self.components[n[0]], tuples))
    
    def hittingset_to_formula(self, tuples):
        """
        this method allows to convert a hitting set back to a fully-fledged LTL formula again, 
        which means that starting from the original formula, the modes in the hitting set are 
        used to replace the corresponding subformulae with their fault mode. Note that this is 
        just for debugging and output purposes, so some small hacks are acceptable :)
        """
        mode_assignment = dict((self.components[t[0]].id,t[1]) for t in tuples)
        f_mapping = {}
        for sf in get_all_subformulas(self.spec, Type.ANY):
            f_mapping[sf.id] = sf
        f = self.spec.clone()
        for sf in get_all_subformulas(f, Type.ANY):
            if sf.id in mode_assignment:
                try:
                    new = self.de.fault_modes[f_mapping[sf.id]][mode_assignment[sf.id]]
                except:
                    print "whowooo"
                if type(new) == Node:
                    # this is a HACK!
                    orig = self.de.fault_modes[f_mapping[sf.id]][0]
                    perm = [orig.children.index(v) for v in new.children]
                    sf.type = new.type
                    sf.children = [sf.children[v] for v in perm]
                    sf.value = new.value
                    sf.instmode = new.instmode
                elif new == True:
                    sf.type = Type.Constant
                    sf.children = []
                    sf.value = "True"
        return f
    
    def print_mapping(self):
        for i in self.components:
            print i, self.components[i]
            if self.components[i] in self.de.fault_modes:
                for j,f in enumerate(self.de.fault_modes[self.components[i]]):
                    print "\t", j, f
            
            
class FaultModeConflictSetHittingSetDescription(FaultModeHittingSetDescription):
    """
    Like its base class, but just uses the FmConflictSet class from the top of this file. 
    Therefore the mapping methods need to be adjusted slightly. 
    """
    pass

    def tuples_to_mode_assignment(self, tuples):
        return dict((self.components[t[0]],t[1]) for t in tuples)
    
    def nodes_to_tuples(self, nodes):
        top = set()
        bot = set()
        for n,m in nodes:
            if m == 0:
                top.add((self.components.key(n), m))
            else:
                bot.add((self.components.key(n), m))
        return FmConflictSet(top,bot)
