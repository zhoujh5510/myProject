
class Description(object):
    """
    Contains the description of a SAT problem
    """

    def __init__(self, variables = [], sentences = []):
        self.variables = variables
        self.sentences = sentences
        
    def add_sentences(self, new_sentences):
        self.sentences.extend(new_sentences)
    
    def get_sentences(self):
        return self.sentences
    
    def get_variables(self):
        return self.variables
    
class Sentence(object):
    
    def __init__(self):
        pass
    
class SimpleDescription(object):
    
    def __init__(self, cnf, num_vars, num_clauses, **options):
        self.cnf = cnf
        self.num_vars = num_vars
        self.num_clauses = num_clauses
        self.options = options
        
class ClauseSentence(Sentence):
    def __init__(self, clause, weight = None):
        self.clause = clause
        self.weight = weight

    def to_yices(self, engine):
        if len(self.clause) > 1:
            return "(assert (or " + " ".join(map(str,self.clause)) + "))"
        elif len(self.clause) > 0:
            return "(assert " + " ".join(map(str,self.clause)) + ")"
        else:
            return ""
        
class WeightSentence(Sentence):
    def __init__(self, clause, weight = None):
        self.clause = clause
        self.weight = weight

    def to_yices(self, engine):
        engine.register_core_sentence(None, self.clause[0])
        return "(assert+ (not " + " ".join(map(str,self.clause)) + ") " + str(self.weight) + ")"
     

class BlockingClauseSentence(Sentence):
    def __init__(self, clause):
        self.clause = clause

    def to_yices(self, engine):
        if len(self.clause) > 1:
            return "(assert (or " + " ".join(map(str,self.clause)) + "))"
        elif len(self.clause) > 0:
            return "(assert " + " ".join(map(str,self.clause)) + ")"
        else:
            return ""
        
