from collections import defaultdict
import sys
import time

class GDE(object):
    
    """
    implements a very simple version of the hitting set algorithm behind the GDE diagnosis algorithm 
    (de Kleer and Williams 1987: Diagnosing Multiple Faults). Note that there is NO predication algorithm 
    /ATMS or whatsoever here. 
    This code is based on the pseudo-code in "A Generalized Minimal Hitting-Set Algorithm to Handle 
    Diagnosis With Behavioral Modes" (Mattias Nyberg, 2011) - Algorithm 1.   
    """


    def __init__(self, oracle, handle=None, options={}):
        self.oracle = oracle
        self.options = options
        self.delta = handle
        self.scs = None
        self.min_card = options.get('min_card',1)
        self.max_card = options.get('max_card',sys.maxint)
        self.max_time = options.get('max_time',None)
        
    def start(self):
        max_time = self.max_time
        
        if max_time:
            end_time = time.time() + max_time
        else:
            end_time = None
            
        self.scs = list(self.oracle.get_conflict_sets())
        if not self.delta:
            self.delta = defaultdict(list)
            for c in self.scs[0]:
                self.delta[1] += [(frozenset([c]),0)]

        csi = 0
        for cs in self.scs[1:]:
            csi += 1
            self.gde(cs, csi)
            if (end_time and time.time() > end_time) or len(self.delta) == 0:
                break
            
        result = set()
        for lst in self.delta.values():
            for sol, _ in lst:
                result.add(frozenset(sol))
        return result
            
    def gde(self, c, idx):

        for card in self.delta.keys():
            if card > self.max_card:
                continue
            
            delta_card = self.delta[card]
#            while self.delta[card]:
            i = 0
            while i < len(delta_card):
#                if self.delta[card][0][1] >= idx:
#                    break
                
#                delta_i, _ = self.delta[card].pop(0) # maybe use queues here and their popleft() method
                delta_i = delta_card[i][0]
                
                if len(delta_i & c) == 0:
                    del delta_card[i]
                    if len(delta_i) < self.max_card:
                        for c_i in c:
                            delta_new = delta_i | frozenset([c_i])
    #                        if len(delta_new) <= self.max_card:
                            found_subset = False
                            for k in self.delta:
                                if k < len(delta_new):
                                    for delta_k, _ in self.delta[k]:
                                        if delta_k <= delta_new:
                                            found_subset = True
                                            break
                            
                            if not found_subset: 
                                self.delta[len(delta_new)].append((delta_new, idx))
                        
                    #end for c_i
                else:
#                    self.delta[len(delta_i)].append((delta_i, idx))
                    delta_card[i] = (delta_i,idx)
                    i = i + 1


