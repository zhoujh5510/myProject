from util.helper import enum
import random
import types

Type = enum('Spec', 'Identifier', 'Constant', 'BoolOr', 'BoolAnd', 'BoolNot', 'BoolXor', 'Until', 'Next', 'WeakUntil', 'Release', 
            'Finally', 'Globally', 'Implies', 'Equivalent', 'Trace', 'TraceStem', 'TraceLoop', 'TraceStep', 'ANY')

InstrumentationMode = enum('Instrument', 'OmitNode', 'OmitSubtree')

InstrumentationModePrettyPrint = {InstrumentationMode.Instrument : "", InstrumentationMode.OmitNode: "$", InstrumentationMode.OmitSubtree : "$$"}

OP_PRECEDENCE = [Type.BoolNot, Type.Next, Type.Until, Type.Release, Type.WeakUntil, Type.Globally, Type.Finally, Type.BoolXor, Type.BoolAnd, Type.BoolOr, Type.Implies, Type.Equivalent]

"""
Used by Node.str to get back the string representation of a syntax tree. Note that (perhaps unnecessary)
parentheses are introduced to make sure that no ambiguity problem is introduced by wrong operator priorities 
in the parsing process. 
"""
str_representation = {
     Type.Spec               : lambda n:     ". ".join([str(c) for c in n.children]) + ".", 
     Type.Identifier         : lambda n:     n.value,
     Type.Constant           : lambda n:     n.value,
     Type.BoolOr             : lambda n:     "(%s ||%s %s)"    % (n.children[0], n.pp_instmode(), n.children[1]),
     Type.BoolAnd            : lambda n:     "(%s &&%s %s)"    % (n.children[0], n.pp_instmode(), n.children[1]),
     Type.BoolNot            : lambda n:     "!%s%s" % (n.pp_instmode(), str(n.children[0])) if n.left.type==Type.Identifier else "(!%s(%s))" % (n.pp_instmode(), n.children[0]),
     Type.BoolXor            : lambda n:     "(%s ^%s  %s)"     % (n.children[0], n.pp_instmode(), n.children[1]),
     Type.Until              : lambda n:     "(%s U%s  %s)"     % (n.children[0], n.pp_instmode(), n.children[1]),
     Type.Next               : lambda n:     "(X%s(%s))"         % (n.pp_instmode(), n.children[0]),
     Type.WeakUntil          : lambda n:     "(%s W%s  %s)"     % (n.children[0], n.pp_instmode(), n.children[1]),
     Type.Release            : lambda n:     "(%s R%s  %s)"     % (n.children[0], n.pp_instmode(), n.children[1]),
     Type.Finally            : lambda n:     "(F%s(%s))"         % (n.pp_instmode(), n.children[0]),
     Type.Globally           : lambda n:     "(G%s(%s))"         % (n.pp_instmode(), n.children[0]),
     Type.Implies            : lambda n:     "(%s =>%s %s)"    % (n.children[0], n.pp_instmode(), n.children[1]),
     Type.Equivalent         : lambda n:     "(%s ==%s %s)"   % (n.children[0], n.pp_instmode(), n.children[1]),
     Type.Trace              : lambda n:     "(%s)"          % " ".join([str(c) for c in n.children]), 
     Type.TraceStem          : lambda n:     "<%s>"          % ";".join([str(c) for c in n.children]), 
     Type.TraceLoop          : lambda n:     "<%s>"          % ";".join([str(c) for c in n.children]), 
     Type.TraceStep          : lambda n:     ",".join([str(c) for c in n.children]), 
     'default'               : lambda n:     n.type + '(' + ",".join(map(str, n.children)) + ')' 
}

"""
This is used by Node.pretty_print and tries to avoid all unnecessary parentheses and still produce a 
string, which, when parsed back, results in the same syntax tree as given as input. Be aware that this 
mechanism relies on the correctness of the OP_PRECEDENCE list above and is subject to bugs introduced 
by changing the general parsing mechanism, i.e. its operator precedences. 
If you want a reliable representation use the normal str() operation with the representations above. 
Note that this representation does not reproduce the instrumentation specifiers ($, $$)!
"""
pretty_str_representation = {
    Type.Spec               : lambda n:     ", ".join(["%s" for _ in n.children]), 
    Type.Identifier         : lambda n:     n.value,
    Type.Constant           : lambda n:     n.value,
    Type.BoolOr             : lambda n:     "%s || %s",
    Type.BoolAnd            : lambda n:     "%s && %s",
    Type.BoolNot            : lambda n:     "!%s",
    Type.BoolXor            : lambda n:     "%s ^ %s",
    Type.Until              : lambda n:     "%s U %s",
    Type.Next               : lambda n:     "X %s",
    Type.WeakUntil          : lambda n:     "%s W %s",
    Type.Release            : lambda n:     "%s R %s",
    Type.Finally            : lambda n:     "F %s",
    Type.Globally           : lambda n:     "G %s",
    Type.Implies            : lambda n:     "%s => %s",
    Type.Equivalent         : lambda n:     "%s <=> %s",
    Type.Trace              : lambda n:     "%s" % " ".join(["%s" for _ in n.children]), 
    Type.TraceStem          : lambda n:     "<%s>" % ";".join(["%s" for _ in n.children]), 
    Type.TraceLoop          : lambda n:     "<%s>" % ";".join(["%s" for _ in n.children]), 
    Type.TraceStep          : lambda n:     ",".join(["%s" for _ in n.children]), 
    'default'               : lambda n:     n.type + '(' + ",".join("%s") + ')' 
}

class Node(object):
    
    """
    The basic node object used to represent the syntax tree for an LTL formula. As the syntax also allows 
    a trace to be specified It is also used to represent traces. 
    The attributes are:
    * children: a list of child nodes, this builds the tree
    * value: an optional value, e.g. for identifier nodes this gives the identifier itself (like "request1" or "a")
    * type: a Type object (see top of this file) representing the type of the node, e.g. Type.Identifier
    * id: a integer number unique upon the syntax tree, which can be used by a user class to identify node objects 
      by other means than their object identity (which might change, e.g. if nodes are cloned)
    * instmode: an optional enum which can be used to "mark" parts of the syntax tree, e.g. here used to mark 
      nodes which should/should not be instrumented later on for diagnosis purposes. See InstrumentationMode type 
      above.   
    """
    
    __slots__ = ['children', 'value', 'type', 'id', 'instmode', 'polarity', 'attributes']
    
    next_id = 1
    
    def __init__(self, type, *children, **fields):
        self.type = type
        self.children = list(children)
        self.value = fields.get('value',None)
        self.id = Node.next_id
        self.instmode = fields.get('instmode', InstrumentationMode.Instrument)
        self.polarity = fields.get('polarity', None)
        self.attributes = fields.get('attributes', None)
        for f in fields:
            if f not in self.__slots__:
                setattr(self, f, fields[f])
        Node.next_id += 1 
        
    def __getattr__(self, name):
        if self.attributes is not None and name in self.attributes:
            return self.attributes[name]
        else:
            return None
    
    def __setattr__(self, name, value):
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        else:
            if self.attributes is None:
                object.__setattr__(self, 'attributes', {})
            if value is not None:
                self.attributes[name] = value
            else:
                if name in self.attributes:
                    del self.attributes[name]
                    
    def __repr__(self):
        return self.__class__.__name__ + "(" + ", ".join(map(lambda f: str(f) + '=' + getattr(self, f).__repr__(), self.__slots__)) + ")"

    def __str__(self):
        return str_representation.get(self.type, str_representation['default'])(self)

    def pretty_print(self):
        result = pretty_str_representation.get(self.type, pretty_str_representation['default'])(self)
        children = list(self.children)
        
        if self.type == Type.BoolOr and self.left.type == Type.BoolNot:
            result = "%s -> %s"
            children = [self.left.inner, self.right]
        
        c_str = []
        for c in children:
            if c.type in OP_PRECEDENCE and OP_PRECEDENCE.index(c.type) > OP_PRECEDENCE.index(self.type):
                c_str += ["(" + c.pretty_print() + ")"]
            else:
                c_str += [c.pretty_print()]
        templates = result.count("%s")
        result = result % tuple(c_str[:templates])
        return result

    def set_id(self,id):
        self.id = id
        return self

    @property
    def pp(self):
        return self.pretty_print()
    
    @property
    def length(self):
        """
        returns the length of the formula represented by this node (i.e. the number of nodes)
        this is equivalent to the sum of number of literals and number of operators in the formula
        
        >>> Identifier("p").length
        1
        
        >>> BoolNot(BoolAnd(Identifier("p"),Identifier("q"))).length
        4
        
        >>> BoolOr(BoolNot(Identifier("p")),BoolNot(Identifier("q"))).length
        5
        
        For traces, the length is the number of trace steps.
        """
        if self.type == Type.TraceLoop or self.type == Type.TraceStem:
            return len(self.children)
        elif self.type == Type.Trace:
            return len(self.stem)+len(self.loop)
        else:
            return sum(map(lambda c: c.length, self.children))+1

    def clone(self, new_ids=False):
        """ 
        returns a copy of this node and all it's children. if new_ids is true, each clone is assigned a new id, 
        otherwise the ids of the original nodes are retained.  
        """
        n = Node(self.type, *[c.clone(new_ids) for c in self.children], value=self.value,instmode=self.instmode)
        if not new_ids:
            n.set_id(self.id)
        return n

    @property
    def left(self):
        return self.children[0]
    
    @property
    def right(self):
        return self.children[1]
    
    @property
    def inner(self):
        return self.children[0]
    
    # especially for traces
    @property
    def stem(self):
        return self.children[0]
    
    @property
    def loop(self):
        return self.children[1]
    
    def __len__(self):
        return self.length

    def __iter__(self):
        return iter(self.children)
    
    def __getitem__(self, key):
        return self.children[key]

    # shortcuts
    @property
    def l(self): #left child
        return self.left

    @property
    def r(self): # right child
        return self.right
    
    # for single-child nodes
    @property
    def i(self): # inner child
        return self.left
        
    def pp_instmode(self):
        return InstrumentationModePrettyPrint.get(self.instmode, "")

    def propagate_omit_subtree(self, omit=False):
        """
        propagates the $$ state (omit complete subtree instrumentation) to 
        the child nodes in the corresponding subtree, by marking each child 
        as $ (omit node instrumentation) recursively. 
        """
        for n in self.children:
            if self.instmode == InstrumentationMode.OmitSubtree or omit == True:
                n.instmode = InstrumentationMode.OmitNode
                omit = True
            n.propagate_omit_subtree(omit)
                
    def propagate_polarity(self, pol=True):
        self.polarity = pol
        if self.type == Type.BoolNot:
            self.i.propagate_polarity(not pol)
        elif self.type == Type.Implies:
            self.l.propagate_polarity(not pol)
            self.r.propagate_polarity(pol)
        elif self.type in [Type.Equivalent, Type.BoolXor]:
            return
        else:
            for n in self.children:
                n.propagate_polarity(pol)
        
    def propagate_parent(self, parent=None):
        self.parent = parent
        for n in self.children:
            n.propagate_parent(self)
        
    def propagate_level(self, level=0):
        self.level = level
        for n in self.children:
            n.propagate_level(level + 1)
            
    def clear_marked(self):
        self.marked = None
        for n in self.children:
            n.clear_marked()

def number_nodes(f):
    ids = {}
    def number(n, h, i):
        h[n] = i
        i += 1
        for c in n.children:
            i = number(c, h, i) + 1
        return i
    number(f, ids, 0)
    return ids
            
        
            
class NodeTransformation(object):
    
    """
    A NodeTransformation object can be used to save sort of a "diff" to an node object, 
    which can be applied afterwards. The node_id is used to identify the node where 
    the patch is applied and a derived class can implement arbitrary changes to this node.
    The find_node method can be used by the derived class to find the target node in a 
    subtree. 
    """
    
    def __init__(self, node_id):
        self.node_id = node_id
        
    def find_node(self, subtree):
        nodes = dict((sf.id, sf) for sf in get_all_subformulas_list(subtree, Type.ANY))
        return nodes[self.node_id]
    
class NodeTypeTransformation(NodeTransformation):
    
    """
    applies a type transformation to a node, see NodeTransformation above, 
    e.g. BoolAnd -> BoolOr
    """
    def __init__(self, node_id, new_type):
        super(NodeTypeTransformation, self).__init__(node_id)
        self.new_type = new_type
        
    def apply(self, subtree):
        n = self.find_node(subtree)
        n.type = self.new_type
        
    def __repr__(self):
        return "NodeTypeTransformation(%d,%s)" % (self.node_id, self.new_type)
        
class NodeValueTransformation(NodeTransformation):
    
    """
    applies a value transformation to a node, see NodeTransformation above, 
    e.g. "a" -> "b"
    """
    def __init__(self, node_id, new_value):
        super(NodeValueTransformation, self).__init__(node_id)
        self.new_value = new_value
        
    def apply(self, subtree):
        n = self.find_node(subtree)
        n.value = self.new_value   
                  
    def __repr__(self):
        return "NodeValueTransformation(%d,%s)" % (self.node_id, self.new_value)
    
class NodeChildOrderTransformation(NodeTransformation):
    
    """
    applies a child order transformation to a node, see NodeTransformation above, 
    children can be reordered by specifying new_order as a list of indices, e.g. 
    using [1,0] would result a && b to be transformed into b && a. 
    """
    def __init__(self, node_id, new_order):
        super(NodeChildOrderTransformation, self).__init__(node_id)
        self.new_order = new_order
        
    def apply(self, subtree):
        n = self.find_node(subtree)
        n.children = [n.children[v] for v in self.new_order]       

    def __repr__(self):
        return "NodeChildOrderTransformation(%d,%s)" % (self.node_id, self.new_order)
    

def syntactic_equivalent(node1, node2, check_instmode=False):
    """
    
    checks two subtrees for syntactic equivalence, e.g. if they represent the very same LTL formula. this 
    can be used to check if two formula are equivalent even if they are from two different parser runs (and 
    have different node identities and Node.id values). note that syntactic equivalence does have anything to do 
    with semantic equivalence or equisatisfiability...
    
    >>> syntactic_equivalent(Identifier("p"),Identifier("p"))
    True
    
    >>> syntactic_equivalent(BoolAnd(Identifier("p"),Identifier("q")),BoolAnd(Identifier("p"),Identifier("q")))
    True
    
    >>> syntactic_equivalent(BoolAnd(Identifier("p"),Identifier("q")),BoolAnd(Identifier("q"),Identifier("p")))
    False
    
    >>> syntactic_equivalent(Spec(Until(Until(BoolAnd(Identifier('a'),Identifier('b')),Identifier('c'),),Identifier('d'))), \
                             Spec(Until(Until(BoolAnd(Identifier('a'),Identifier('b')),Identifier('c')),Identifier('d'))))
    True
    
    >>> syntactic_equivalent(CFalse(), CTrue())
    False
    
    """
    if node1.type == node2.type and node1.value == node2.value and len(node1.children) == len(node2.children) and \
        (node1.attributes == node2.attributes or node1.attributes is None and node2.attributes == {} or node1.attributes == {} and node2.attributes is None) and \
        (node1.instmode == node2.instmode or not check_instmode):
        return all([syntactic_equivalent(node1.children[i], node2.children[i]) for i in range(len(node1.children))])
    else:
        return False

def diff_formulas(f1, f2):
    """
    returns those subtrees from the formula f1 which are not equivalent in f2.
    """
    r = []
    if not syntactic_equivalent(f1, f2):
        r.append(f1)
    else:
        for i in xrange(len(f1.children)):
            r.extend(diff_formulas(f1.children[i], f2.children[i]))
    return r
    

def get_all_subformulas(formula, type):
    return set([formula] if (formula.type == type or type == Type.ANY) else []).union(*[get_all_subformulas(c, type) for c in formula.children])

def get_all_subformulas_list(formula, t):
    """
    returns as a list all those subformulas from the given formula which are selected by t, where t can be 
    * a method or lambda: in this case the method is passed the subformula and can decide whether to return it or not
    * a Node type (ltlparser.ast.Type) or the special type Type.ANY, in which case all subformulas of this type 
    (or all, respectively) are returned
    """
    if type(t) == types.FunctionType:
        r = []
        if t(formula):
            r.append(formula)
        for c in formula.children:
            r.extend(get_all_subformulas_list(c, t))
        return r
    else:
        r = []
        if (formula.type == t or t == Type.ANY):
            r.append(formula)
        for c in formula.children:
            r.extend(get_all_subformulas_list(c, t))
        return r
    
def num_differences(f1,f2):

    """
    The number of nodes that differ in f1 and f2. Note that also the node id is respected.
    This is mainly used to check that a random mutation process indeed resulted in the intended number of mutations.  
    """
    f1_sf = set(map(lambda sf: (sf.id, sf.type, sf.value, sf.instmode), get_all_subformulas_list(f1, Type.ANY)))
    f2_sf = set(map(lambda sf: (sf.id, sf.type, sf.value, sf.instmode), get_all_subformulas_list(f2, Type.ANY)))
    diff = f1_sf - (f1_sf & f2_sf)
    return len(diff)

def randomize_ids(formula):
    """
    assign new Node.id values to the given formula nodes
    """
    subformulas = get_all_subformulas_list(formula, Type.ANY)
    ids = map(lambda node: node.id, subformulas)
#    print "Before:", ids
    new_ids = list(ids)
    random.shuffle(new_ids)
    for sf in subformulas:
        sf.id = new_ids[ids.index(sf.id)]
#    subformulas = get_all_subformulas_list(formula, Type.ANY)
#    ids = map(lambda node: node.id, subformulas)
#    print "After: ", ids
    

# some shorthands

def Spec(*formulae, **fields):
    return Node(Type.Spec, *formulae, **fields)

def Identifier(value, **fields):
    return Node(Type.Identifier, value=value, **fields)

def Constant(value, **fields):
    return Node(Type.Constant, value=value, **fields)

def CTrue(**fields):
    fields['value'] = "True"
    return Node(Type.Constant, **fields)

def CFalse(**fields):
    fields['value'] = "False"
    return Node(Type.Constant, **fields)

def BoolOr(left, right, **fields):
    return Node(Type.BoolOr, left, right, **fields)

def BoolAnd(left, right, **fields):
    return Node(Type.BoolAnd, left, right, **fields)

def BoolNot(c, **fields):
    return Node(Type.BoolNot, c, **fields)

def BoolXor(left, right, **fields):
    return Node(Type.BoolXor, left, right, **fields)

def Until(left, right, **fields):
    return Node(Type.Until, left, right, **fields)

def Next(c, **fields):
    return Node(Type.Next, c, **fields)

def WeakUntil(left, right, **fields):
    return Node(Type.WeakUntil, left, right, **fields)

def Release(left, right, **fields):
    return Node(Type.Release, left, right, **fields)

def Finally(c, **fields):
    return Node(Type.Finally, c, **fields)

def Globally(c, **fields):
    return Node(Type.Globally, c, **fields)
    
def Implies(left, right, **fields):
    return Node(Type.Implies, left, right, **fields)

def Equivalent(left, right, **fields):
    return Node(Type.Equivalent, left, right, **fields)

def Trace(stem, loop):
    return Node(Type.Trace, stem, loop)

def TraceStem(*children):
    return Node(Type.TraceStem, *children)

def TraceLoop(*children):
    return Node(Type.TraceLoop, *children)

def TraceStep(*children):
    return Node(Type.TraceStep, *children)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
