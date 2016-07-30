
class Description(object):
    '''
    This class stores the input for a model checking computation, where typically 
    automata should contain a (list of) automata.automaton.GBA, specification and traace 
    an ltlparser.ast.Node.
    '''

    def __init__(self, automata=None, specification=None, trace=None, **options):
        '''
        '''
        self.options = options
        self.automata = automata
        self.specification = specification
        self.trace = trace
        
    def set_options(self, **options):
        self.options.update(options)

