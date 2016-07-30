

class Result(object):
    '''
    Contains the result of a model checking problem, where ``sat'' says if the specification was met, 
    stats contains some statistics and trace optionally contains a witness if it has been calculated. 
    '''

    def __init__(self, sat, trace=None, **stats):
        '''
        Constructor
        '''
        self.sat = sat
        self.stats = stats
        self.trace = trace
        
    def __repr__(self):
        return "Result(%s, %s)" % (self.sat, self.trace)