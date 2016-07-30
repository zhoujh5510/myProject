class Result(object):
    """
    Represents the result of a SAT calculation. 
    A Result object states whether the SAT problem was satisfiable or not, a valuation for 
    the variables as returned by the SAT solver (in the SAT case), or an unsatisfiable core 
    if the SAT engine can calculate such (in the UNSAT case).   
    """

    def __init__(self, satisfiable, values, unsat_core):
        self.satisfiable = satisfiable
        self.values = values
        self.unsat_core = unsat_core
        
    def sat(self):
        return self.satisfiable == True
    
    def unsat(self):
        return not self.sat()
    
    def get_values(self):
        return self.values
    
    def get_unsat_core(self):
        return self.unsat_core
    
    def __repr__(self):
        return "sat.Result: %s, %s, %s" % (self.satisfiable, self.values, self.unsat_core)