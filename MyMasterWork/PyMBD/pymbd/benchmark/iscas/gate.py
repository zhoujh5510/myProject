
class Gate(object):
    """
    >>> Gate('11gat', 'nand', ['x1', 'x3'])
    Gate('11gat', 'nand', ['x1', 'x3'])
    
    If you "unpack" a Gate instance, you can use it to construct 
    a copy, e.g.
    >>> Gate(*Gate('11gat', 'nand', ['x1', 'x3']))
    Gate('11gat', 'nand', ['x1', 'x3'])
    """
    
    def __init__(self, output, type, inputs):
        self.output = output
        self.type = type
        self.inputs = inputs
    
    def __iter__(self):
        return iter([self.output, self.type, self.inputs])
        
    def __repr__(self):
        return "Gate('%s', '%s', %s)" % (self.output, self.type, self.inputs)
        
if __name__ == "__main__":
    import doctest
    doctest.testmod()