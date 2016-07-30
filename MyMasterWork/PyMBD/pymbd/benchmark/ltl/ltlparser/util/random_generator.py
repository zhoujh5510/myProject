from ..ast import Type, Node, BoolNot, Trace, TraceStem, TraceLoop, \
    TraceStep, get_all_subformulas_list, InstrumentationMode, NodeTypeTransformation, \
    NodeValueTransformation
import random

TERMINALS       = set([Type.Identifier, Type.Constant])
UNARY_OPS       = set([Type.BoolNot, Type.Next, Type.Finally, Type.Globally]) 
BINARY_OPS      = set([Type.BoolOr, Type.BoolAnd, Type.BoolXor, Type.Until, Type.WeakUntil, Type.Release, Type.Implies, Type.Equivalent]) # 
TEMPORAL_OPS    = set([Type.Until, Type.WeakUntil, Type.Release, Type.Finally, Type.Globally, Type.Next]) #  
BASIC_OPS       = set([Type.BoolAnd, Type.BoolOr, Type.BoolNot, Type.Next, Type.Until, Type.Release])

BINARY_BOOL_OPS = BINARY_OPS - TEMPORAL_OPS
BINARY_TEMP_OPS = BINARY_OPS & TEMPORAL_OPS
UNARY_BOOL_OPS  = UNARY_OPS - TEMPORAL_OPS
UNARY_TEMP_OPS  = UNARY_OPS & TEMPORAL_OPS

def generate_random_ltl_formula(length, num_vars, temporal_prob, only_basic_ops=False, include_constants=False, exclude_ops=set([Type.WeakUntil])):
    """
    
    This generates random LTL formulae using a method like described in "Improved automata generation for linear temporal logic" (Daniele, 
    Giunchiglia, Vardi) section 5. Depending on the remaining length of the formula to be generated a corresponding unary or binary operator 
    is generated or the method is called recursively. The flags only_basic_ops, include_constants and the exclude_ops set allow to 
    specify which elements the generated formula should feature, the temporal_prob probability specifies the probability that a temporal 
    operator is selected in a certain step. 
    If new operator are introduced they must be added to the sets above to be considered in the generation process.  
    
    >>> generate_random_ltl_formula(10, 3, 0.33).length
    10
    
    >>> generate_random_ltl_formula(111, 10, 0.33).length
    111
    
    >>> generate_random_ltl_formula(1, 1, 0.33).length
    1

    >>> generate_random_ltl_formula(2, 1, 0.33).length
    2
    
    >>> generate_random_ltl_formula(10, 3, 0.33, True).length
    10
    
    >>> generate_random_ltl_formula(111, 10, 0.33, True).length
    111
    """
    if length == 1:
        t = Type.Identifier if not include_constants else random.choice(list(TERMINALS))
        if t == Type.Identifier:
            v = "v" + str(random.randint(1,num_vars))
            return Node(t, value=v)
        elif t == Type.Constant:
            v = random.choice(["True", "False"])
            return Node(t, value=v)
        else:
            raise Exception("unkown choice")
    elif length == 2:
        t = random.choice(list((UNARY_OPS & BASIC_OPS)-exclude_ops)) if only_basic_ops else random.choice(list(UNARY_OPS-exclude_ops))
        c = generate_random_ltl_formula(length-1, num_vars, temporal_prob, only_basic_ops, include_constants, exclude_ops)
        return Node(t, c)
    else:
        if random.uniform(0,1) < temporal_prob:
            t = random.choice(list((TEMPORAL_OPS & BASIC_OPS)-exclude_ops)) if only_basic_ops else random.choice(list(TEMPORAL_OPS-exclude_ops))
            if t in UNARY_OPS:
                c = generate_random_ltl_formula(length-1, num_vars, temporal_prob, only_basic_ops, include_constants, exclude_ops)
                return Node(t, c)
            elif t in BINARY_OPS:
                s = random.randint(1,length-2)
                c1 = generate_random_ltl_formula(s, num_vars, temporal_prob, only_basic_ops, include_constants, exclude_ops)
                c2 = generate_random_ltl_formula(length-s-1, num_vars, temporal_prob, only_basic_ops, include_constants, exclude_ops)
                return Node(t, c1, c2)
            else:
                raise Exception("unknown choice")
        else:
            t = random.choice(list(((UNARY_OPS | BINARY_OPS) & BASIC_OPS)-exclude_ops)) if only_basic_ops else random.choice(list((UNARY_OPS | BINARY_OPS)-exclude_ops))
            if t in UNARY_OPS:
                c = generate_random_ltl_formula(length-1, num_vars, temporal_prob, only_basic_ops, include_constants, exclude_ops)
                return Node(t, c)
            elif t in BINARY_OPS:
                s = random.randint(1,length-2)
                c1 = generate_random_ltl_formula(s, num_vars, temporal_prob, only_basic_ops, include_constants, exclude_ops)
                c2 = generate_random_ltl_formula(length-s-1, num_vars, temporal_prob, only_basic_ops, include_constants, exclude_ops)
                return Node(t, c1, c2)
            else:
                raise Exception("unknown choice")
    

def generate_random_trace(variables, stem_length, loop_length):
    """
    Generates a random trace of given length (stem length and loop length) where the variables in the given set 
    are true in a certain time step with probability 0.5 and false otherwise (i.e. a fully specified trace).
    """
    def gen_part(length):
        part = []
        for unused_i in range(length):
            step = []
            for v in variables:
                if random.uniform(0,1) > 0.5:
                    step += [BoolNot(v)]
                else:
                    step += [v]
            part += [TraceStep(*step)]
        return part
                    
    return Trace(TraceStem(*gen_part(stem_length)), TraceLoop(*gen_part(loop_length)))

    

def inject_random_faults(formula, num_faults=1, already_mutated_sf=set(), **fault_types):
    """
    Injects num_faults into the given formula by replacing operators or exchanging identifier names, e.g.
    injecting 3 faults into 
    
    ((G((g1 => (X((!g1 U  r1)))))) &&$ (G((g2 => (X((!g2 U  r2)))))))
    
    could result in
    
    ((G((g1 == (X((!g1 U  r1)))))) &&$ (G((g2 => (G((!g1 U  r2)))))))
             ^                                    ^    ^
    
    Nodes annotated as being not instrumented ($/$$) are not mutated (e.g. the && above). 
    """
#    print "Already mutated:", already_mutated_sf
    sf_operators = get_all_subformulas_list(formula, lambda x: x.id not in already_mutated_sf and x.type != Type.Identifier 
                                                       and x.type != Type.Constant and x.type != Type.BoolNot
                                                       and x.instmode == InstrumentationMode.Instrument)
    
    sf_identifiers = get_all_subformulas_list(formula, lambda x: x.id not in already_mutated_sf and x.type == Type.Identifier 
                                           and x.instmode == InstrumentationMode.Instrument)
    
    mutations = {'mutate_operators':True, 'mutate_variables':True}
    mutations.update(fault_types)
    
    if len(set(map(lambda sf: sf.value, sf_identifiers))) < 2:
        mutations['mutate_variables'] = False # cannot mutate if just one variable
    
    if len(sf_operators) < 1:
        mutations['mutate_operators'] = False
        
    if len([name for name,value in mutations.iteritems() if value == True]) == 0:
#        print "Problem injecting fault into formula", formula
        return []
        
    chosen_mutation = random.choice([name for name,value in mutations.iteritems() if value == True])
    
    transformations = []
    
    if num_faults > 0:
        if chosen_mutation == 'mutate_operators':

            done = False
            while not done:
                mutated_sf = random.choice(sf_operators)
                for x in get_all_subformulas_list(mutated_sf, Type.ANY):
#                    print "Adding subformula", x
                    already_mutated_sf.add(x.id)
#                print "mutating", mutated_sf
                ops = [BINARY_TEMP_OPS,BINARY_BOOL_OPS,UNARY_TEMP_OPS] # UNARY_BOOL_OPS has only Type.Not -> no mutation possible
                for op in ops:
                    if mutated_sf.type in op:
                        mutated_sf.type = random.choice(list(op - set([mutated_sf.type])))
                        transformations += [NodeTypeTransformation(mutated_sf.id, mutated_sf.type)]
                        done = True
                        break
                if done:
#                    print "Adding", mutated_sf
                    already_mutated_sf.add(mutated_sf.id)
                    while mutated_sf.parent:
                        already_mutated_sf.add(mutated_sf.parent.id)
#                        print "Adding parent", mutated_sf.parent
                        mutated_sf = mutated_sf.parent
                    
        if chosen_mutation == 'mutate_variables':

            mutated_sf = random.choice(sf_identifiers)
            for x in get_all_subformulas_list(mutated_sf, Type.ANY):
#                print "Adding subformula", x
                already_mutated_sf.add(x.id)
            sf_identifiers.remove(mutated_sf)
            sf_identifiers = [sf for sf in sf_identifiers if sf.value != mutated_sf.value]
            new_var = random.choice(sf_identifiers)
            mutated_sf.value = new_var.value
            transformations += [NodeValueTransformation(mutated_sf.id, mutated_sf.value)]
#            print "Adding", mutated_sf
            already_mutated_sf.add(mutated_sf.id)
            while mutated_sf.parent:
                already_mutated_sf.add(mutated_sf.parent.id)
#                print "Adding parent", mutated_sf.parent
                mutated_sf = mutated_sf.parent

                    
        if num_faults > 1:
            transformations += inject_random_faults(formula, num_faults-1, already_mutated_sf, **fault_types)
    return transformations


if __name__ == "__main__":
    import doctest
    doctest.testmod()
    r = generate_random_ltl_formula(1000, 300, 0.33, True)
    print r
    # write_pdf(dotTree(r), "random.pdf")
    