
def merge(opts1, opts2):
    return dict(opts1.items() + opts2.items())

ENGINES = { }


class Engine(object):
    '''
    Encapsules an algorithm that does the actual model checking computation. 
    This implementation does nothing, derived classes must implement at least 
    the start() method and place a Result object in self.result at the end
    '''

    def __init__(self, description, options):
        '''
        Construct a model checking computation engine from the problem description. 
        An options hash specific to the algorithm  may be given as second parameter. 
        '''
        self.description = description
        self.options = options
        self.result = None
        self.handle = None
        
    def start(self):
        pass
    
    def get_result(self):
        return self.result
    
    def set_options(self, options):
        self.options.update(options)
