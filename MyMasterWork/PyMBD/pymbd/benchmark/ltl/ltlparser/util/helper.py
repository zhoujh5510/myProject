
def enum(*sequential, **named):
    """
    Creates a custom enumeration type from the given sequence, where the elements of the sequence are converted to class attributes. 
    If unnamed arguments are used, the name and value of the attributes are the same, otherwise the value can be specified explicitly. 
    e.g. 
    
    T = enum('a','b','c') would create a type T with T.a being "a", T.b being "b" and so on. The type T then is sort of a type-safe 
    enum, e.g. a comparison like foobar == T.d would result in an error rather than staying unmatched silently, other than when using 
    strings directly. 
    
    The named variant could look like T = enum(a=1, b=2, c=3), which would the use the number as values, e.g. T.a is 1.   
    """
    enums = dict(zip(sequential, sequential), **named)
    return type('Enum', (), enums)


def flatten(l, ltypes=(list, tuple)):
    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], ltypes):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i + 1] = l[i]
        i += 1
    return ltype(l)

def write_ast(formula, filename, highlight_nodes=[], highlight_attribs={}, lbl_func=None, id_func=None, label=""):
    write_pdf(dotTree(formula, highlight_nodes, highlight_attribs, lbl_func, id_func), filename, label)

def write_pdf(tree, filename, label=""):
    tree.set_label(label)
    tree.set_labelloc = "t"
#    tree.write(filename + ".dot")
    tree.write_pdf(filename)

def dotTree(root, highlight_nodes=[], highlight_attribs={}, lbl_func=None, id_func=None):
    import pydot
    import pygraphviz as pgv
    
    if not lbl_func:
        lbl_func = lambda node: str(node.type) + ('&#10;' + node.value if node.value else "")
    if not id_func:
        id_func = lambda node: id(node)
    
    def dotNode(g, node):
        attr_list = {'label' : lbl_func(node)}
        if node in highlight_nodes:
#            attr_list['color'] = 'red'
#            attr_list['shape'] = 'doublecircle'
            attr_list['style'] = 'filled'
            attr_list.update(highlight_attribs)
        newNode = pydot.Node(str(id_func(node)), **attr_list)
        g.add_node(newNode)
        if node.children:
            for i,c in enumerate(node.children):
#                attr_list = {'label' : "L" if i == 0 else "R" if i == 1 else str(i), 'margin':0, 'nodesep':0.5, 'ranksep':0.5}
                attr_list = {'style': 'dashed' if i == 0 and str(node.type) in ["Until", "WeakUntil", "Release", "Implies"] else 'solid'}
                if not g.get_edge(str(id_func(node)), str(id_func(c))):
                    newEdge = pydot.Edge(str(id_func(node)), str(id_func(c)), **attr_list)
                    g.add_edge(newEdge)
                dotNode(g, c)
            
    
    g = pydot.Dot()
    g.set_type('digraph')
    g.set_graph_defaults(**{'nodesep':0.3,'ranksep':0.3})
    dotNode(g, root)
    return g


def print_trace(trace):
    steps = trace.stem.children + trace.loop.children
    vars = sorted(set().union(*[set([v.value if not v.children else v.i.value for v in s]) for s in steps]))
    f_width = max(len("id "),max(map(len,vars)))
    print 
#    print (f_width+2*len(trace)+2) * "=",
    for f in map(str,vars):
        print
        print str(f).ljust(f_width),  
        for i in range(len(trace)):
            if i == len(trace.stem):
                print "|", 
            print "T" if any(map(lambda v: v.value == f, steps[i])) else "_", 
    print
    print
    
def polarity_label_func(node):
    return str(node.type) + (" (+)" if node.polarity is True else (" (-)" if node.polarity is False else " (0)")) + ('&#10;' + node.value if node.value else "")

def print_trace_filtered(trace):
    print "<",
    for step in trace.stem.children:
        for var in step:
            if str(var.type) == "Identifier":
                print var.value,
        print "  ;  ",
    print ">",
    print "<",
    for step in trace.loop.children:
        for var in step:
            if str(var.type) == "Identifier":
                print var.value,
        print "  ;  ",
    print ">"
    

def trace_as_vis_constraint(trace):
    res = "{True}|+>{{"
    sep2 = ""
    for step in trace.stem.children:
        res += sep2
        sep2 = ";"
        res += "{"
        sep = ""
        
        part = ""
        for var in step:
            part += sep
            part += "{" + (var.value if var.type == "Identifier" else "!"+var.i.value) + "}"
            sep = ":"
            part = "{" + part + "}"
        
        res += part
        res += "}"
        
    res += "};{"
    sep2 = ""
    res += "{"
    for step in trace.loop.children:
        res += sep2
        sep2 = ";"
        res += "{"
        sep = ""
        part = ""
        for var in step:
            part += sep
            part += "{" + (var.value if var.type == "Identifier" else "!"+var.i.value) + "}"
            sep = ":"
            part = "{" + part + "}"
        
        res += part
        res += "}"

    res += "}[*]"
    res += "}}"
    
    return res

def pretty_lbl_func(node):
    str_representation = {
         "Identifier"         : lambda n:     n.value,
         "Constant"           : lambda n:     n.value,
         "BoolOr"             : lambda n:     "or",
         "BoolAnd"            : lambda n:     "and",
         "BoolNot"            : lambda n:     "not",
         "BoolXor"            : lambda n:     "xor",
         "Until"              : lambda n:     "U",
         "Next"               : lambda n:     "X",
         "WeakUntil"          : lambda n:     "W",
         "Release"            : lambda n:     "R",
         "Finally"            : lambda n:     "F",
         "Globally"           : lambda n:     "G",
         "Implies"            : lambda n:     "=>",
         "Equivalent"         : lambda n:     "<=>",
         "Trace"              : lambda n:     "(%s)"          % " ".join([str(c) for c in n.children]), 
         "TraceStem"          : lambda n:     "<%s>"          % ";".join([str(c) for c in n.children]), 
         "TraceLoop"          : lambda n:     "<%s>"          % ";".join([str(c) for c in n.children]), 
         "TraceStep"          : lambda n:     ",".join([str(c) for c in n.children]), 
         'default'            : lambda n:     n.type + '(' + ",".join(map(str, n.children)) + ')' 
    }
    return str(node.level) + ": n" + str(node.id) + ": " + str_representation.get(str(node.type), str_representation['default'])(node)