'''
Created on Jan 10, 2013

@author: tq
'''
import time

class MaxSatDiagnosis(object):
    
    '''
    This algorithm implements "MERIDIAN" from "Solving Model-Based Diagnosis Problems with Max-SAT Solvers and Vice Versa" (Feldman et al. 2010)
    '''
    
    def __init__(self, oracle, previous_solutions=None, **options):
        self.oracle = oracle
        self.previous_solutions=previous_solutions
        self.options = options
        self.oracle.set_options(**options)
        self.time_map = {}
        self.start_time = None
        self.timeout = False
    
    def start(self):
        max_time = self.options.get('max_time', None)
        max_card = self.options.get('max_card',None)
        reuse_sat = self.options.get('reuse_sat', True)
        self.start_time = time.time()
        max_num_solutions = self.options.get('max_num_solutions', None)
        
        if max_time:
            end_time = time.time() + max_time
        else:
            end_time = None
        
        last_diag = set()
        result = set()
        
        if self.previous_solutions:
            new_diag = self.oracle.get_next_diagnosis(self.previous_solutions)
        else:
            new_diag = self.oracle.get_next_diagnosis(set())
        found_time = time.time()
        
        while 1:
            
            if end_time and  time.time() > end_time:
                self.timeout = True
                break
            
            if not new_diag:
#                print "No further diagnoses found."
#                new_diag = frozenset()
#                new_diag = self.oracle.get_next_diagnosis([last_diag])
                break
            
            if max_card and len(new_diag) > max_card:
                break
            
            if max_num_solutions is not None and len(self.time_map) >= max_num_solutions:
                break
        
#            print "Found diagnosis:", new_diag
            result |= set([new_diag])
            self.time_map[new_diag] = found_time - self.start_time
        
            if reuse_sat:
                last_diag = new_diag
                new_diag = self.oracle.get_next_diagnosis([last_diag])
            else:
                new_diag = self.oracle.get_next_diagnosis(result)

        return result
    
    
