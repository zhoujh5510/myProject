'''
Created on Jan 23, 2013

@author: tq
'''
from ..sat.description import SimpleDescription
from ..sat.problem import Problem
from ..util.two_way_dict import TwoWayDict
import time
    
class SatHs(object):
    
    '''
    This algorithm implements 
    '''
    
    def __init__(self, oracle, **options):
        self.oracle = oracle
        self.options = options
        self.oracle.set_options(**options)
        self.time_map = {}
        self.start_time = None
        self.timeout = False
        self.sat_solver = self.options.get('sat_solver', 'simple-scryptominisat-async')
        self.sat_problem = None
        self.mapping = None
    
    def start(self):
        max_time = self.options.get('max_time', None)
        max_card = self.options.get('max_card',None)

#        reuse_sat = self.options.get('reuse_sat', True)
        self.start_time = time.time()
        max_num_solutions = self.options.get('max_num_solutions', None)
        
        scs = self.oracle.scs
        comp = self.oracle.components
        
        if max_card:
            max_card = min(max_card, len(scs), len(comp))
        else:
            max_card = min(len(scs), len(comp))
        
        self.mapping = TwoWayDict(dict(enumerate(comp,1)))
        mapping = self.mapping
        
        cnf = ["\n".join([" ".join(map(str,[self.mapping.get_key(l) for l in c] + [0])) for c in scs])]
        
        if max_time:
            end_time = time.time() + max_time
        else:
            end_time = None
        
        result = set()
        card = 1
        new_hs = self.get_hitting_sets(cnf, len(self.mapping), len(scs), card)
        found_time = time.time()
        
        while 1:
            
            if end_time and  time.time() > end_time:
                self.timeout = True
                break

            if max_num_solutions is not None and len(self.time_map) >= max_num_solutions:
                break
        
            if new_hs:
                cnf += ["\n".join([" ".join(map(str,[-l for l in c] + [0])) for c in new_hs])]
                result |= set([frozenset([mapping[l] for l in h]) for h in new_hs])
                for d in new_hs:
                    self.time_map[frozenset(d)] = found_time - self.start_time

            card += 1
        
            if card > max_card:
                break
            
            new_hs = self.get_hitting_sets(cnf, len(self.mapping), len(scs), card)
        
        return result

    def get_hitting_sets(self, cnf, num_vars, num_clauses, max_card):
        sd = SimpleDescription(cnf, num_vars, num_clauses, get_valuation=True)
        if not self.sat_problem:
            self.sat_problem = Problem(self.sat_solver)
            r = self.sat_problem.solve(sd, weighted=False, ab_vars=self.mapping.keys(), max_card=max_card, find_all_sols=True, max_out=num_vars)
        else:
            r = self.sat_problem.solve_again(sd, weighted=False, ab_vars=self.mapping.keys(), max_card=max_card, find_all_sols=True, max_out=num_vars)
        return r
