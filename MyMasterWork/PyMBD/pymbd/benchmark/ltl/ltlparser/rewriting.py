from ast import Type, CTrue, CFalse, BoolNot, syntactic_equivalent, \
    Equivalent, Identifier, Finally, Until, Globally, BoolOr, Release, BoolXor, \
    BoolAnd, Implies, WeakUntil, get_all_subformulas, InstrumentationMode
from parser import parse
from util.helper import write_pdf, dotTree

"""
The functions in this module are used to rewrite various syntactic elements, e.g. syntactic 
sugar like F and G to their equivalents using U. But also simpler operations like transformations
from a == True to a and a == False to !a are possible.
Each method can be used separately and will do its modifications live on the given AST instance. 
While methods can be applied successively, note that each one iterates over the complete syntax 
tree. So if you need a fast rewriting of several actions you should combine them to your own 
method. 
"""

def neg(expr):
    """
    >>> syntactic_equivalent(neg(CTrue()), CFalse())
    True
    
    >>> syntactic_equivalent(neg(Identifier("p")), BoolNot(Identifier("p")))
    True
    
    >>> syntactic_equivalent(neg(BoolNot(Identifier("q"))), Identifier("q"))
    True
    
    >>> syntactic_equivalent(neg(CFalse()), CTrue())
    True
    """
    
    if expr.type == Type.BoolNot:
        return expr.left
    elif expr.type == Type.Constant:
        if expr.value == CTrue().value:
            return CFalse()
        else:
            return CTrue()
    else:
        return BoolNot(expr)


def replace(n1, n2):
    n1.type = n2.type
    n1.value = n2.value
    n1.children = n2.children

def rewrite_istrue_isfalse(node):
    """
    Rewrites propositions like p=1 or q=0 into p and !q, respectively. 
    
    >>> syntactic_equivalent(rewrite_istrue_isfalse(Equivalent(Identifier("p"), CTrue())), Identifier("p"))
    True

    >>> syntactic_equivalent(rewrite_istrue_isfalse(Equivalent(Identifier("p"), CFalse())), BoolNot(Identifier("p")))
    True

    >>> syntactic_equivalent(rewrite_istrue_isfalse(Equivalent(CTrue(), Identifier("p"))), Identifier("p"))
    True

    >>> syntactic_equivalent(rewrite_istrue_isfalse(Equivalent(CFalse(), Identifier("p"))), BoolNot(Identifier("p")))
    True

    """
    for n in node.children:
        rewrite_istrue_isfalse(n)
    if node.type == Type.Equivalent:
        if node.left.type == Type.Constant and node.left.value == "True":
            replace(node, node.right)
        elif node.right.type == Type.Constant and node.right.value == "True":
            replace(node, node.left)
        elif node.left.type == Type.Constant and node.left.value == "False":
            node.type = Type.BoolNot
            node.children = [node.right]
        elif node.right.type == Type.Constant and node.right.value == "False":
            node.type = Type.BoolNot
            node.children = [node.left]
    return node

def rewrite_not_true_not_false(node):
    """
    rewrites !True to False and !False to True
    
    >>> syntactic_equivalent(rewrite_not_true_not_false(BoolNot(CTrue())), CFalse())
    True

    >>> syntactic_equivalent(rewrite_not_true_not_false(BoolNot(CFalse())), CTrue())
    True
    
    """
    for n in node.children:
        rewrite_not_true_not_false(n)
    if node.type == Type.BoolNot:
        inner = node.left
        if inner.type == Type.Constant and inner.value == "True":
            replace(node, CFalse())
        elif inner.type == Type.Constant and inner.value == "False":
            replace(node, CTrue())
    return node

def rewrite_finally(node):
    
    """
    rewrites finally into the until equivalent
    
    >>> syntactic_equivalent(rewrite_finally(Finally(Identifier("p"))), Until(CTrue(),Identifier("p")))
    True
    
    """
    
    for n in node.children:
        rewrite_finally(n)
        
    if node.type == Type.Finally:
        node.type = Type.Until
        node.children = [CTrue(), node.left]
    
    return node

def rewrite_globally(node):
    """
    rewrites globally into the until equivalent 
    
    >>> syntactic_equivalent(rewrite_globally(parse("G p")), parse("~(True U ~p)"))
    True
    
    >>> syntactic_equivalent(rewrite_globally(parse("G F p")), parse("~(True U ~(F p))"))
    True
    
    >>> syntactic_equivalent(rewrite_globally(rewrite_finally(parse("G F p"))), parse("~(True U ~(true U p))"))
    True

    >>> syntactic_equivalent(rewrite_globally(rewrite_finally(parse("G F p"))), rewrite_finally(rewrite_globally(parse("G F p"))))
    True
    
    """
    for n in node.children:
        rewrite_globally(n)
        
    if node.type == Type.Globally:
        node.type = Type.BoolNot
        node.children = [Until(CTrue(), BoolNot(node.left))]
    
    return node

def rewrite_release(node):
    """
    rewrites release into its until equivalent 
    
    >>> syntactic_equivalent(rewrite_release(parse("a R b")), parse("~(~a U ~b)"))
    True
    
    """
    for n in node.children:
        rewrite_release(n)
        
    if node.type == Type.Release:
        node.type = Type.BoolNot
        node.children = [Until(BoolNot(node.left), BoolNot(node.right))]
    
    return node

def rewrite_nnf(node):
    """
    rewrites to negational normal form (all not operators which are not in front of an atom 
    are pushed inside).
    
    >>> syntactic_equivalent(rewrite_nnf(parse("!(p and q)")), parse("!p or !q"))
    True

    >>> syntactic_equivalent(rewrite_nnf(parse("!(p or q)")), parse("!p && !q"))
    True

    >>> syntactic_equivalent(rewrite_nnf(parse("!!p")), parse("p"))
    True

    >>> syntactic_equivalent(rewrite_nnf(parse("!(p -> q)")), parse("p && !q"))
    True
    
    >>> syntactic_equivalent(rewrite_nnf(parse("!(A -> (B && !(C || D)))")), parse("A && (!B || (C || D))"))
    True
    
    >>> syntactic_equivalent(rewrite_nnf(parse("!(p <-> q)")), parse("(!p || !q) && (p || q)"))
    True

    >>> syntactic_equivalent(rewrite_nnf(parse("!G(f)")), parse("True U !f"))
    True
    
    >>> syntactic_equivalent(rewrite_nnf(parse("!F(f)")), parse("false R !f"))
    True
    
    >>> syntactic_equivalent(rewrite_nnf(parse("!(a U b)")), parse("!a R !b"))
    True
    
    >>> syntactic_equivalent(rewrite_nnf(parse("!(a R b)")), parse("!a U !b"))
    True
    
    >>> syntactic_equivalent(rewrite_nnf(parse("!(X a)")), parse("X !a"))
    True
    
    >>> syntactic_equivalent(rewrite_nnf(parse("!(a W b)")), parse("(!a R !b) && (True U !a)"))
    True
    
    """
    
    while node.type == Type.BoolNot and node.left.type == Type.BoolNot:
        replace(node, node.left.left)
    
    if node.type == Type.BoolNot:
        inner = node.left
        if inner.type == Type.Identifier or inner.type == Type.Constant:
            pass            
        elif inner.type == Type.BoolAnd:
            node.type = Type.BoolOr
            node.children = [BoolNot(inner.left), BoolNot(inner.right)]
        elif inner.type == Type.BoolOr:
            node.type = Type.BoolAnd
            node.children = [BoolNot(inner.left), BoolNot(inner.right)]
        elif inner.type == Type.Implies:
            node.type = Type.BoolAnd
            node.children = [inner.left, BoolNot(inner.right)]
        elif inner.type == Type.Equivalent:
            node.type = Type.BoolAnd
            node.children = [BoolOr(BoolNot(inner.left), BoolNot(inner.right)), BoolOr(inner.left, inner.right)]
        elif inner.type == Type.Globally:
            node.type = Type.Until
            node.children = [CTrue(), BoolNot(inner.left)]
        elif inner.type == Type.Finally:
            node.type = Type.Release
            node.children = [CFalse(), BoolNot(inner.left)]
        elif inner.type == Type.Until:
            node.type = Type.Release
            node.children = [BoolNot(inner.left), BoolNot(inner.right)]
        elif inner.type == Type.Release:
            node.type = Type.Until
            node.children = [BoolNot(inner.left), BoolNot(inner.right)]           
        elif inner.type == Type.Next:
            node.type = Type.Next
            node.children = [BoolNot(inner.left)]          
        elif inner.type == Type.WeakUntil:
            node.type = Type.BoolAnd
            node.children = [Release(BoolNot(inner.left), BoolNot(inner.right)), Until(CTrue(), BoolNot(inner.left))] 

    for n in node.children:
        rewrite_nnf(n)

    return node

def rewrite_xor(node):
    """
    rewrites xor to the and/or equivalent 
    
    >>> syntactic_equivalent(rewrite_xor(BoolXor(Identifier("p"), Identifier("q"))), BoolAnd(BoolOr(BoolNot(Identifier("p")), BoolNot(Identifier("q"))), BoolOr(Identifier("p"), Identifier("q"))))
    True
    
    """
    
    for n in node.children:
        rewrite_xor(n)
        
    if node.type == Type.BoolXor:
        node.type = Type.BoolAnd
        node.children = [BoolOr(BoolNot(node.left), BoolNot(node.right)), BoolOr(node.left, node.right)]
    
    return node

def rewrite_implies(node):
    """
    rewrites implies (->) to the or equivalent
    
    >>> syntactic_equivalent(rewrite_implies(Implies(Identifier("p"), Identifier("q"))), BoolOr(BoolNot(Identifier("p")), Identifier("q")))
    True
    
    """
    
    for n in node.children:
        rewrite_implies(n)
        
    if node.type == Type.Implies:
        node.type = Type.BoolOr
        node.children = [BoolNot(node.left), node.right]
    
    return node


def rewrite_weakuntil(node):
    """
    rewrites weak until into its until equivalent 
    
    >>> syntactic_equivalent(rewrite_weakuntil(parse("a W b")), parse("(a U b) || (false R a)"))
    True
    
    """
    
    for n in node.children:
        rewrite_weakuntil(n)
        
    if node.type == Type.WeakUntil:
        node.type = Type.BoolOr
        node.children = [Until(node.left, node.right), Release(CFalse(), node.left)] 
    
    return node

def rewrite_equivalent(node):
    """
    rewrites equivalent (<->) into its and/or equivalent
    
    >>> syntactic_equivalent(rewrite_equivalent(Equivalent(Identifier("p"), Identifier("q"))), BoolAnd(BoolOr(BoolNot(Identifier("p")), Identifier("q")), BoolOr(Identifier("p"), BoolNot(Identifier("q")))))
    True
    
    """
    
    for n in node.children:
        rewrite_equivalent(n)
        
    if node.type == Type.Equivalent:
        node.type = Type.BoolAnd
        node.children = [BoolOr(BoolNot(node.left), node.right), BoolOr(node.left, BoolNot(node.right))]
    
    return node

def is_nnf(node):
    """
    
    Returns true if the given formula is in negational normal form, i.e. if all Boolean NOT operators are 
    only in front of identifiers (atoms)
    
    >>> is_nnf(parse("a"))
    True

    >>> is_nnf(parse("!a"))
    True

    >>> is_nnf(parse("!a and !b"))
    True

    >>> is_nnf(parse("!(a and !b)"))
    False
    
    >>> is_nnf(parse("!(A -> (B && !(C || D)))"))
    False
 
    >>> is_nnf(parse("A && (!B || (C || D))"))
    True
    
    >>> is_nnf(parse("G(!F(x))"))
    False
    
    """
    for n in node.children:
        if not is_nnf(n):
            return False
    if node.type == Type.BoolNot:
        inner = node.left
        return inner.type == Type.Identifier or inner.type == Type.Constant
    return True


def rewrite_to_simpleform(node):
    """
    combines several rewriters to obtain a form where only the very basic Boolean and temporal operators 
    are used. 
    
    >>> syntactic_equivalent(rewrite_to_simpleform(parse("F(G(G(True)))")), parse("true U (false R (false R true))"))
    True
    """
    f = node.clone()
    rewriters = [rewrite_istrue_isfalse, rewrite_xor, rewrite_implies, rewrite_weakuntil, rewrite_equivalent, rewrite_finally, rewrite_globally, rewrite_nnf, rewrite_not_true_not_false]
    for r in rewriters:
        f = r(f)
#        print r.__name__, "->", f
    return f

def rewrite_extended_booleans(node):
    """
    combines several operators which remove all Boolean operators except AND and OR and replace the corresponding 
    subformulas by equivalent expressions. 
    """
    f = node.clone()
    rewriters = [rewrite_istrue_isfalse, rewrite_xor, rewrite_implies, rewrite_equivalent, rewrite_not_true_not_false]
    for r in rewriters:
        f = r(f)
#        print r.__name__, "->", f
    return f


def rewrite_to_dag(node):
    """
    rewrites the given syntax tree into a directed acyclic graph, which means that nodes that are syntactically equivalent 
    and occur multiple times in the tree are replaced by one representative object. 
    """
    def unique(nodes):
        drop = []
        for i in nodes:
            for j in nodes:
                if i != j and syntactic_equivalent(i,j) and j not in drop and i not in drop:
                    drop.append(j)
        for d in drop:
            nodes.remove(d)
        return nodes
    
    def traverse(node):
        for i,c in enumerate(node.children):
            traverse(c)
            for n in all_nodes:
                if n != c and syntactic_equivalent(n, c):
#                    print hash(n), "!=", hash(c)
#                    print "replacing", node.children[i], "with", n
                    node.children[i] = n
        return node
             
    all_nodes = unique(get_all_subformulas(node, Type.ANY))
    return traverse(node)

def rewrite_spec(node):
    """
    The syntax allows to specify multiple specification (parts) using the dot syntax, e.g. 
    "G(a). G(b).", where the dot actually means a Boolean AND. This rewriter thus converts these
    Type.Spec nodes into the Type.BoolAnd nodes but marks them as "not instrumented", because 
    we don't want any diagnosis results involving these AND nodes. 
    """
    for n in node.children:
        rewrite_spec(n)
        
    if node.type == Type.Spec:
        if len(node.children) > 2:
            new = BoolAnd(node.children[0], node.children[1], instmode=InstrumentationMode.OmitNode)
            for c in node.children[2:]:
                new = BoolAnd(new, c, instmode=InstrumentationMode.OmitNode)
            return new
        else:
            node.type = Type.BoolAnd
            node.instmode = InstrumentationMode.OmitNode
            return node
    else:
        return node

#write_pdf(dotTree(rewrite_xor(parse("(a*b) ^ (b*c)"))), "test-input.pdf")
#write_pdf(dotTree(rewrite_nnf(parse("!F(a)"))), "test-found.pdf")
#write_pdf(dotTree(rewrite_nnf(parse("False R !a"))), "test-expected.pdf")

if __name__ == "__main__":
    import doctest
    doctest.testmod()
    