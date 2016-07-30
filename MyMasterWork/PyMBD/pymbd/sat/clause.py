from literal import lit

class Clause(object):
    
    """
    >>> Clause([Literal('a', False), Literal('b', True)]) == Clause([Literal('b', True), Literal('a', False)])
    True
    """
    
    def __init__(self, literals, weight=None):
        self.literals = literals
        self.weight = weight

    def __repr__(self):
        return str(self.literals)

    def __cmp__(self, other):
        return set(self.literals) == set(other.literals) and self.weight == other.weight # the order of literals doesn't matter since they are ORed together
    
def clause(string):
    """
    shorthand for constructing a clause by hand
    >>> clause("a b !c")
    [a, b, !c]
    """
    return Clause(map(lambda l: lit(l), string.strip().split(" ")))

def clauses(string):
    """
    shorthand for constructing a sequences of clauses by hand
    >>> clauses("a b !c, b !a c")
    [[a, b, !c], [b, !a, c]]
    """
    return map(lambda c: clause(c.strip()), string.split(","))

if __name__ == "__main__":
    import doctest
    doctest.testmod()
    