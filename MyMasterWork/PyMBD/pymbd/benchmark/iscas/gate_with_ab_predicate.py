from gate import Gate
from pymbd.util.sethelper import powerset
from pymbd.sat import yices, picosat, scryptominisat
from pymbd.sat.clause import clause
from pymbd.sat.description import Sentence

class GateWithAbPredicate(Sentence):
    """
    Represents the fault injection logic used to enable/disable a gate's function. 
    The implication ab_predicate -> gate_function  
    """
    
    def __init__(self, ab_predicate, gate):
        self.ab_predicate = ab_predicate
        self.gate = gate
        
    def __repr__(self):
        return "(!%s => %s)" % (self.ab_predicate, self.gate)

class GateSentence(Sentence):
    
    def __init__(self, gate):
        self.gate = gate
        
## ------------------------------------ yices specific code ------------------------------------

def xor(inputs):
    """
    Produces yices-syntax code for an XOR for multiple input variables. 
    
    >>> xor(['x1', 'x2'])
    '(or (and x1 (not x2)) (and (not x1) x2))'
    
    >>> xor(['x1', 'x2', 'x3'])
    '(or (and x1 x2 x3) (and x1 (not x2) (not x3)) (and (not x1) (not x2) x3) (and (not x1) x2 (not x3)))'
    
    """
    if len(inputs) == 2:
        code = '(or (and ' + inputs[0] + ' (not ' + inputs[1] + ')) (and (not ' + inputs[0] + ') ' + inputs[1] + '))'
    else:
        # the output of a multi-input xor is true if an odd number of inputs is true
        code = "(or"
        comb = filter(lambda c: len(c) % 2 == 1, powerset(inputs))
        for c in comb:
            code += " (and"
            for i in inputs:
                if i in c:
                    code += " " + i
                else:
                    code += ' (not ' + i + ')'
            code += ")"
        code += ")"
    return code

# These lambda expressions return yices-syntax code for the basic gates used in the ISCAS networks  

AB_PREDICATE = "(assert (=> (not {ab}) {gate}))" 
GATES = {
    'nand' : lambda output, inputs: '(= {output} (not (and {inputs})))'.format(output=output, inputs=" ".join(inputs)),
    'nor'  : lambda output, inputs: '(= {output} (not (or  {inputs})))'.format(output=output, inputs=" ".join(inputs)),
    'not'  : lambda output, inputs: '(= {output} (not      {inputs}) )'.format(output=output, inputs=" ".join(inputs)),
    'and'  : lambda output, inputs: '(= {output}      (and {inputs}) )'.format(output=output, inputs=" ".join(inputs)),
    'or'   : lambda output, inputs: '(= {output}      (or  {inputs}) )'.format(output=output, inputs=" ".join(inputs)),
    'xor'  : lambda output, inputs: '(= {output}           {xor}     )'.format(output=output, xor=xor(inputs)),
    'xnor' : lambda output, inputs: '(= {output} (not      {xor}    ))'.format(output=output, xor=xor(inputs)),
    'buff' : lambda output, input:  '(= {output} {input})'.format(output=output, input=" ".join(input))
}
ASSERT = "(assert {gate})"

def gate_with_ab_predicate(ab, gate):
    """
    Returns a sentence/assertion (whatever you call it) in yices-syntax for the given gate using an AB predicate. 
    
    >>> gate_with_ab_predicate('ABn1', Gate('x10', 'nand', ['x1', 'x3']))
    '(=> (not ABn1) (= x10 (not (and x1 x3))))'
    
    >>> gate_with_ab_predicate('ABn1', Gate('x10', 'xnor', ['x1', 'x3']))
    '(=> (not ABn1) (= x10 (not      (or (and x1 (not x3)) (and (not x1) x3))    )))'
    """
    if gate.type in GATES:
        g = GATES[gate.type](gate.output, gate.inputs)
        return AB_PREDICATE.format(ab=ab, gate=g)
    else:
        return "; unknown gate: %s" % gate

def gate(gate):
    """
    Returns a sentence/assertion (whatever you call it) in yices-syntax for the given gate.
    
    >>> gate(Gate('x10', 'nand', ['x1', 'x3']))
    '(= x10 (not (and x1 x3)))'
    
    >>> gate(Gate('x10', 'xnor', ['x1', 'x3']))
    '(= x10 (not      (or (and x1 (not x3)) (and (not x1) x3))    ))'
    """
    if gate.type in GATES:
        g = GATES[gate.type](gate.output, gate.inputs)
        return ASSERT.format(gate=g)
    else:
        return "; unknown gate: %s" % gate


yices.SENTENCE_INTERPRETERS[GateWithAbPredicate] = lambda engine, p, unused: gate_with_ab_predicate(p.ab_predicate, p.gate)
yices.SENTENCE_INTERPRETERS[GateSentence]        = lambda engine, p, unused: gate(p.gate)


## ------------------------------------ PicoSat specific code ------------------------------------

def all_neg(literals):
    """
    >>> all_neg(['x1', 'x2', 'x3'])
    '!x1 !x2 !x3'
    >>> all_neg(['x1'])
    '!x1'
    """
    return "!" + " !".join(literals)

def all_pos(literals):
    return " ".join(literals)

def neg(literal):
    return " !" + literal

def pos(literal):
    return " " + literal

def clauses_gate_with_ab_predicate(ab, gate):
    c = CNF[gate.type](gate)
    return map(lambda i: clause(i + pos(ab)), c)

def clauses_gate(gate):
    c = CNF[gate.type](gate)
    return map(lambda i: clause(i), c)

CNF = {
    # these are the CNFs of the boolean functions used as gates, i.e. for 
    # c <=> a OP b. 
    # obtained using wolframalpha.com (just enter c <=> (a xor b) for example)
    # Note that nand, nor, and and or have been extended to work with multiple inputs
    
    # For AND, in logic notation, the CNF would be (LaTeX)
    # z \Leftrightarrow \bigwedge_i x_i \equiv \left( \bigvee_i (\neg x_i) \vee z \right) \wedge \left(\bigwedge_i (x_i \vee \neg z) \right)
    
    'nand' : lambda gate: [all_neg(gate.inputs) + neg(gate.output)] + map(lambda input: pos(input) + pos(gate.output), gate.inputs),
    'nor'  : lambda gate: [all_pos(gate.inputs) + pos(gate.output)] + map(lambda input: neg(input) + neg(gate.output), gate.inputs),
    'and'  : lambda gate: [all_neg(gate.inputs) + pos(gate.output)] + map(lambda input: pos(input) + neg(gate.output), gate.inputs),
    'or'   : lambda gate: [all_pos(gate.inputs) + neg(gate.output)] + map(lambda input: neg(input) + pos(gate.output), gate.inputs),
    'xor'  : lambda gate: map(lambda x: x % {'a': gate.inputs[0], 'b': gate.inputs[1], 'c': gate.output}, 
                              ["!%(a)s !%(b)s !%(c)s", "!%(a)s %(b)s %(c)s", "%(a)s !%(b)s %(c)s", "%(a)s %(b)s !%(c)s"]),
    'xnor' : lambda gate: map(lambda x: x % {'a': gate.inputs[0], 'b': gate.inputs[1], 'c': gate.output}, 
                              ["!%(a)s !%(b)s %(c)s", "!%(a)s %(b)s !%(c)s", "%(a)s !%(b)s !%(c)s", "%(a)s %(b)s %(c)s"]),
    'buff' : lambda gate: map(lambda x: x % {'a': gate.inputs[0], 'c': gate.output}, 
                              ["!%(a)s %(c)s", "%(a)s !%(c)s"]),
    'not'  : lambda gate: map(lambda x: x % {'a': gate.inputs[0], 'c': gate.output},
                              ["!%(a)s !%(c)s", "%(a)s %(c)s"])
}
    
picosat.SENTENCE_INTERPRETERS[GateWithAbPredicate] = lambda engine, pred, unused: clauses_gate_with_ab_predicate(pred.ab_predicate, pred.gate)
picosat.SENTENCE_INTERPRETERS[GateSentence]        = lambda engine, pred, unused: clauses_gate(pred.gate)

scryptominisat.SENTENCE_INTERPRETERS[GateWithAbPredicate] = lambda engine, pred, unused: clauses_gate_with_ab_predicate(pred.ab_predicate, pred.gate)
scryptominisat.SENTENCE_INTERPRETERS[GateSentence]        = lambda engine, pred, unused: clauses_gate(pred.gate)

def cnf_gate_with_ab_predicate(ab, gate):
    c = CNF[gate.type](gate)
    return "\n".join(map(lambda i: "(assert (or " + cnf_clause(i) + " " + ab + "))", c))

def cnf_clause(c):
    return " ".join(map(lambda l: cnf_literal(l), clause(c).literals))

def cnf_literal(l):
    return l.name if l.sign else "(not %s)" % l.name

yices.SENTENCE_INTERPRETERS_CNF[GateWithAbPredicate] = lambda engine, pred, unused: cnf_gate_with_ab_predicate(pred.ab_predicate, pred.gate)
yices.SENTENCE_INTERPRETERS_CNF[GateSentence]        = lambda engine, pred, unused: clauses_gate(pred.gate)

yices.SENTENCE_INTERPRETERS_DIMACS[GateWithAbPredicate] = lambda engine, pred, unused: clauses_gate_with_ab_predicate(pred.ab_predicate, pred.gate)
yices.SENTENCE_INTERPRETERS_DIMACS[GateSentence]        = lambda engine, pred, unused: clauses_gate(pred.gate)

yices.SENTENCE_INTERPRETERS_CN[GateWithAbPredicate] = lambda engine, pred, unused: clauses_gate_with_ab_predicate(pred.ab_predicate, pred.gate)
yices.SENTENCE_INTERPRETERS_CN[GateSentence]        = lambda engine, pred, unused: clauses_gate(pred.gate)

yices.SENTENCE_INTERPRETERS_CN_CNF[GateWithAbPredicate] = lambda engine, pred, unused: cnf_gate_with_ab_predicate(pred.ab_predicate, pred.gate)
yices.SENTENCE_INTERPRETERS_CN_CNF[GateSentence]        = lambda engine, pred, unused: clauses_gate(pred.gate)



if __name__ == "__main__":
    import doctest
    doctest.testmod()
    