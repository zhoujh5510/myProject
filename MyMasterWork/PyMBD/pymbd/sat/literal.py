class Literal(object):

    __slots__ = ['name', 'sign']

    def __init__(self, name, sign):
        self.name = name
        self.sign = sign
    def __repr__(self):
        return ("!" if self.sign == False else "") + self.name
        
def lit(nameandvalue):
    """
    constructs a literal using a short syntax, e.g.
    >>> lit('a').name
    'a'
    >>> lit('!b').sign
    False
    """ 
    if nameandvalue[0] == '!':
        return Literal(nameandvalue[1:], False)
    else:
        return Literal(nameandvalue, True)
    
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()
    