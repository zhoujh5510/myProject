ENGINES = { }

class Engine(object):
    """
    Encapsulates a SAT solver engine like MiniSAT (or even yices, ...)
    """

    def __init__(self, options = {}):
        self.handle = None
        self.result = None
        self.sentence_interpreters = {}
        self.variable_interpreters = {}
        self.options = options
    
    def start(self, description, **options):
        self.description = description
        self.set_options(options)
        pass
        
    def start_again(self, new_sentences, **options):
        self.set_options(options)
        pass
        
    def get_result(self):
        return self.result
    
    def set_options(self, options):
        self.options.update(options)
        
    def finished(self):
        pass
    
    def register_core_sentence(self, id, sentence):
        pass