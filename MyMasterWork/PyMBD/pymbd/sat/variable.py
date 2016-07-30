
class Variable(object):
    
    BOOLEAN = 1
    
    def __init__(self, name, type, value):
        self.name = name
        self.type = type
        self.value = value
        
    def __repr__(self):
        return "Variable(%s, %s, %s)" % (self.name, self.type, self.value)
    
    