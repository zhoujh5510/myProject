'''
Created on Jan 10, 2013

@author: tq
'''
from ..sat.description import SimpleDescription, Description, ClauseSentence, \
    WeightSentence, BlockingClauseSentence
from ..sat.problem import Problem
from ..sat.variable import Variable
from ..util.two_way_dict import TwoWayDict
import time

class MaxSatHs(object):
    
    '''
    '''
    
    def __init__(self, oracle, previous_solutions=None, **options):
        self.oracle = oracle
        self.previous_solutions=previous_solutions
        self.options = options
        self.oracle.set_options(**options)
        self.time_map = {}
        self.start_time = None
        self.timeout = False
        self.sat_solver = self.options.get('sat_solver', 'yices-maxsat')
    
    def start(self):
        max_time = self.options.get('max_time', None)
        max_card = self.options.get('max_card',None)
        self.start_time = time.time()
        max_num_solutions = self.options.get('max_num_solutions', None)
        
        if max_time:
            end_time = time.time() + max_time
        else:
            end_time = None
        
        scs = self.oracle.scs
        comp = self.oracle.components

        if max_card:
            max_card = min(max_card, len(scs), len(comp))
        else:
            max_card = min(len(scs), len(comp))
        
        vars = [Variable("v%d"%v, Variable.BOOLEAN, None) for v in comp]
        clauses = [ClauseSentence(["v%d"%c for c in s]) for s in scs]
        clauses += [WeightSentence(["v%d"%c],1) for c in comp]
        descr = Description(vars, clauses)
        
        result = set()
        
        self.sat_problem = Problem(self.sat_solver)
        new_hs = self.sat_problem.solve(descr, weighted=True)
        if new_hs:
            new_hs = frozenset(map(int,new_hs))
        found_time = time.time()
        
        while 1:
            
            if end_time and  time.time() > end_time:
                self.timeout = True
                break
            
            if not new_hs:
                break
            
            if max_card and len(new_hs) > max_card:
                break
            
            if max_num_solutions is not None and len(self.time_map) >= max_num_solutions:
                break
        
#            print "Found diagnosis:", new_diag
            result |= set([new_hs])
            self.time_map[new_hs] = found_time - self.start_time
            
            new_hs = self.sat_problem.solve_again([BlockingClauseSentence(["(not v%s)"%c for c in new_hs])])
            if new_hs:
                new_hs = frozenset(map(int,new_hs))

        return result
