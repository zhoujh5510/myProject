from gate import Gate
from collections import namedtuple
from string import strip

ParseResult = namedtuple('ParseResult', ['input', 'output', 'connections'])

class SimpleParser(object):
    """
    Parses the simple netlist format (.sisc) created by the ISCAS translator (trans.c) from 
    the original .isc files. Returns a namedtuple ParseResult that contains the names of the 
    input variables, the names of the output variables and a list of connections in the form 
    <output> <gate/func> <input> <input> ...
    
    >>> SimpleParser(open('../../iscas-data/c17.sisc')).parse().input
    ['1gat', '2gat', '3gat', '6gat', '7gat']
    
    >>> SimpleParser(open('../../iscas-data/c17.sisc')).parse().output
    ['22gat', '23gat']
    
    >>> SimpleParser(open('../../iscas-data/c17.sisc')).parse().connections[0]
    Gate('10gat', 'nand', ['1gat', '3gat'])
    """
    
    def __init__(self, sisc):
        self.file = sisc
    
    def parse(self):
        return self.parse_from_strings(self.file.readlines())
    
    def parse_from_strings(self, content):
        content = filter(lambda line: not strip(line).startswith('$'), content)
        input   = filter(lambda x: x is not None, map(self.get_inputs, content))
        output  = filter(lambda x: x is not None, map(self.get_outputs, content))
        connections = filter(lambda line: len(strip(line).split()) > 2 and 'primary' not in line, content)
        connections = map(lambda line: line.split(), connections)
        gates = map(lambda line: Gate(line[0], line[1], line[2:]), connections)
        return ParseResult(input, output, gates)
        
    def get_inputs(self, line):
        return self.get_primary(line, "input")
        
    def get_outputs(self, line):
        return self.get_primary(line, "output")
    
    def get_primary(self, line, type):
        line = line.split()
        if 'primary' in line and type in line:
            return line[0] 
        else:
            return None
            
def parse_output(output):
    values = {}
    for r in output:
        l = r.split()
        name = l[1]
        value = l[2][:-1]
        values[name] = True if value == "true" else (False if value == "false" else value)
    return values
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()
    
