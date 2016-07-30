from description import Description
from engine import ENGINES
import random

class Problem(object):
    '''
    Represents a whole model checking computation problem and works as a facade for easier use of 
    the python modules involved. 
    '''

    def __init__(self):
        pass
        
    def compute_with_description(self, description, engine_name, **options):
        '''
        Start the MC computation with the given description object and engine. 
        The exact computation process is determined by the capabilities of the 
        engine and the contents of the description object, e.g. an engine might 
        be able to deal with automata while the other one does not. 
        '''
        randstate = random.getstate()
        self.description = description
        if engine_name not in ENGINES:
            raise Exception("Unknown Model Checking Engine: %s" % engine_name)
        self.engine = ENGINES[engine_name](self.description, options)
        self.engine.start()
        self.result = self.engine.get_result()
        random.setstate(randstate)
        return self.result

#    def compute_counterexample(self, formula, engine_name, **options):
#        '''
#        '''
#        randstate = random.getstate()
#        self.description = Description(None, formula)
#        if engine_name not in ENGINES:
#            raise Exception("Unknown Model Checking Engine: %s" % engine_name)
#        self.engine = ENGINES[engine_name](self.description, options)
#        self.engine.start()
#        self.result = self.engine.get_result()
#        random.setstate(randstate)
#        return self.result
    
    def compute_trace(self, formula, engine_name, **options):
        '''
        Like compute_with_description, but here only a LTL formula is given and a 
        description object is created from it. For the engine this means that a 
        trace fulfilling this formula should be computed. 
        '''
        randstate = random.getstate()
        self.description = Description(None, formula)
        if engine_name not in ENGINES:
            raise Exception("Unknown Model Checking Engine: %s" % engine_name)
        self.engine = ENGINES[engine_name](self.description, options)
        self.engine.start()
        self.result = self.engine.get_result()
        random.setstate(randstate)
        return self.result
    
    