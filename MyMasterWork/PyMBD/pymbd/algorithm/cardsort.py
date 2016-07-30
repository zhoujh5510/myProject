'''
Created on Jan 23, 2013

@author: tq
'''
import time


class CardSortDiagnosis(object):

    '''
    This algorithm implements
    '''

    def __init__(self, oracle, previous_solutions=None, **options):
        self.oracle = oracle
        self.previous_solutions = previous_solutions
        self.options = options
        self.oracle.set_options(**options)
        self.time_map = {}
        self.start_time = None
        self.timeout = False

    def start(self):
        max_time = self.options.get('max_time', None)
        max_card = self.options.get('max_card', None)
        if not max_card:
            print "Must supply max_card option to calculate diagnoses with DirectSatDiagnosis!"
        reuse_sat = self.options.get('reuse_sat', True)
        self.start_time = time.time()
        max_num_solutions = self.options.get('max_num_solutions', None)

        if max_time:
            end_time = time.time() + max_time
        else:
            end_time = None

        last_diag = set()
        result = set()
        card = 1
        if self.previous_solutions:
            card = max(map(len(self.previous_solutions))) + 1
            new_diag = self.oracle.get_next_diagnosis(self.previous_solutions, max_card=card)
        else:
            new_diag = self.oracle.get_next_diagnosis(set(), card)
        found_time = time.time()

        if not new_diag:
            card += 1

        while card <= max_card:

            if end_time and time.time() > end_time:
                self.timeout = True
                break

            if max_num_solutions is not None and len(self.time_map) >= max_num_solutions:
                break

            if new_diag:
#                print "Found diagnosis:", new_diag
                result |= set([new_diag])
                self.time_map[new_diag] = found_time - self.start_time
                last_diag = [new_diag]
            else:
                last_diag = []

            if reuse_sat:
                new_diag = self.oracle.get_next_diagnosis(last_diag, max_card=card)
            else:
                new_diag = self.oracle.get_next_diagnosis(result, max_card=card)
#            print "new_diag", new_diag
            if not new_diag:
                card += 1

        return result


class MultiCardSortDiagnosis(object):
    
    '''
    This algorithm implements 
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
        if not max_card:
            print "Must supply max_card option to calculate diagnoses with DirectSatDiagnosis!"
        reuse_sat = self.options.get('reuse_sat', True)
        self.start_time = time.time()
        
#        print "Algorithm started at %.6f" % time.time()
        
        max_num_solutions = self.options.get('max_num_solutions', None)
        
        if max_time:
            end_time = time.time() + max_time
        else:
            end_time = None
        
        last_diag = set()
        result = set()
        card = 1
        if self.previous_solutions:
            card = max(map(len,self.previous_solutions)) + 1
            new_diag = self.oracle.get_all_diagnoses(self.previous_solutions, max_card=card)
        else:
            new_diag = self.oracle.get_all_diagnoses(set(), card)
        found_time = time.time()
        
        while 1:
            
            if end_time and  time.time() > end_time:
                self.timeout = True
                break

            if max_num_solutions is not None and len(self.time_map) >= max_num_solutions:
                break
        
            if new_diag:
#                print "Found solution:", new_diag
                result |= set(new_diag)
                for d in new_diag:
                    self.time_map[frozenset(d)] = found_time - self.start_time
                last_diag = new_diag
            else:
                last_diag = []

            card += 1
        
            if card > max_card:
                break
            
            if reuse_sat:
                new_diag = self.oracle.get_all_diagnoses(last_diag, max_card=card)
            else:
                new_diag = self.oracle.get_all_diagnoses(result, max_card=card)
#            print "new_diag", new_diag
            
                
#        print "Algorithm finished at %.6f" % time.time()
        
        return result
