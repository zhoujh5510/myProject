from description import SimpleDescription
from engine import ENGINES
import random

class Problem(object):
    """
    Represents a SAT problem. 
    A Description contains the input (a list of sentences, e.g. CNF clauses), which is 
    then handed to an Engine instance, which in turn produces a Result object stating 
    whether the problem was satisfiable or not, a valuation for the variables as returned 
    by the SAT solver (in the SAT case), or an unsatisfiable core if the SAT engine can 
    calculate such (in the UNSAT case).   
    """

    DEFAULT_ENGINE = 'yices'

    def __init__(self, engine_name = None):
        self.solve_called = False
        self.engine_name = engine_name
        self.initialized = False
        self.engine = None
        
    def init_engine(self):
        if not self.initialized:
            self.initialized = True
            if self.engine_name is None:
                self.engine_name = Problem.DEFAULT_ENGINE
            if self.engine_name not in ENGINES:
                raise Exception("Unknown SAT Engine: %s" % self.engine_name)
            options = {}
            self.engine = ENGINES[self.engine_name](options)
    
    def solve(self, description, **options):
        """
        Solves the given SAT problem by handing variables and sentences from
        the description to the SAT engine, which translates them into its 
        custom input format and stores a Result object in self.result. 
        The engine addressed by engine_name must be registered in 
        the sat.engine.Engine.ENGINES hash.   
        """
        # HACK!!!
        if type(description) == SimpleDescription:
            self.engine_name = "simple-" + self.engine_name
        self.init_engine()
        randstate = random.getstate()
        self.solve_called = True
        self.description = description
        self.engine.start(self.description, **options)
        self.result = self.engine.get_result()
        random.setstate(randstate)
        return self.result
    
    def solve_again(self, new_sentences, **options):
        randstate = random.getstate()
        self.engine.start_again(new_sentences, **options)
        self.result = self.engine.get_result()
        random.setstate(randstate)
        return self.result
    
    def finished(self):
        """
        Always make sure that you call this method after you finished using an instance. 
        Some engines may run as a daemon in the background and need to be terminated 
        explicitly. If they are not, their processes may stay orphaned forever. 
        """
        if self.engine:
            self.engine.finished()
        
    
