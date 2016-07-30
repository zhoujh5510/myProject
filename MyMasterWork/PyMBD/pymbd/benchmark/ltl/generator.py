'''
Created on Jun 26, 2012

@author: tq
'''
from pymbd.util.sethelper import powerset
from ltlparser.ast import BoolAnd, BoolNot
from ltlparser.util.random_generator import generate_random_ltl_formula, \
    inject_random_faults
from pymbd.benchmark.ltl.mc.description import Description
from pymbd.benchmark.ltl.mc.problem import Problem

def generate_mutated_formula_and_witness(formula_args=[10, 3, 0.5, False, False, set()], trace_length=(10,5), num_faults=1, **fault_types):
    
    tries_f = 0
    while tries_f < 10:
        tries_f += 1
        f = generate_random_ltl_formula(*formula_args)
#        print "Original:", f
        f.propagate_parent()
        t = None
        tries_t = 0
        while t is None or tries_t < 10:
            tries_t += 1
            trace = Problem().compute_trace(f, 'directsat', trace_length=trace_length).trace
            t = trace.to_trace_formula()
#            print "Trace:", t
            
            d = Description(specification=f, trace=t) 
            r = Problem().compute_with_description(d, 'directsat')
            
            if not r.sat:
                continue
            
            f_orig = f
            tries_m = 0
            while  tries_m < 20:
                tries_m += 1
                f_new = f.clone()
                f_new.propagate_parent()
                transformations = inject_random_faults(f_new, num_faults, set(), **fault_types)
                if len(transformations) != num_faults:
                    print "not enough mutations"
                    continue
#                print "Original:", f
#                print "Mutation:", f_new
#                orig = str(f)
#                new = str(f_new)
#                marker = [" "]*len(max(orig,new))
#                for i in xrange(len(max(orig,new))):
#                    if i < len(orig) and i < len(new) and orig[i] != new[i]:
#                        marker[i] = "^"
#                print "         ", "".join(marker)
#                print
                
                no_subset_sat = True
                subsets = set(list(powerset(transformations))) - set([frozenset()])
#                print len(subsets), subsets
                for transformation in subsets:
                    f_test = f.clone()
                    for tr in transformation:
                        tr.apply(f_test)
                
#                    print "Subset:", len(transformation), f_test, 

                    
                    d = Description(specification=f_test, trace=t)
                    r = Problem().compute_with_description(d, 'directsat')
                    if r.sat:
                        no_subset_sat = False
#                        print "SAT"
#                        print
#                        print
#                        break
#                    else:
#                        print "OK"
#                    orig = str(f)
#                    new = str(f_test)
#                    marker = [" "]*len(max(orig,new))
#                    for i in xrange(len(max(orig,new))):
#                        if i < len(orig) and i < len(new) and orig[i] != new[i]:
#                            marker[i] = "^"
#                    print "         ", "".join(marker)
#                    print
                    if r.sat:
                        break
                    
                    
                if no_subset_sat:
#                    print tries_f, tries_t, tries_m 
                    return f_orig, f_new, t
#                else:
#                    print "transformation set is sat:", tr
                                    
    print "FAILED to create mutated formula"
    

def check_no_subset_sat(f, t, transformations):
    no_subset_sat = True
    subsets = set(list(powerset(transformations))) - set([frozenset()]) - set([frozenset(transformations)])
    for transformation in subsets:
        f_test = f.clone()
        for tr in transformation:
            tr.apply(f_test)
        
        d = Description(specification=f_test, trace=t)
        r = Problem().compute_with_description(d, 'directsat')
        if r.sat:
            return False
#        else:
#            print "subset", transformation, "is not sat"
        
    if no_subset_sat:
        return True
    
    
def generate_mutated_formula_and_witness_2(formula_args=[10, 3, 0.5, False, False, set()], trace_length=(10,5), num_faults=1, **fault_types):
    
    tries_f = 0
    while tries_f < 100:
        tries_f += 1
        f = generate_random_ltl_formula(*formula_args)
        
        f_orig = f.clone(True)
        
#        ids = number_nodes(f)
#        write_ast(f, "multiple_fault.pdf", [], {'fillcolor':'lightblue'}, pretty_lbl_func, lambda n: ids[n], "%d fault(s)"%num_faults)

        tries_m = 0
        while  tries_m < 100:
            tries_m += 1
            f_new = f.clone()
            f_new.propagate_parent()
            transformations = inject_random_faults(f_new, num_faults, set(), **fault_types)
            if len(transformations) != num_faults:
                print "not enough mutations"
                continue
#            print "Original", f
#            print "Mutated ", f_new
            
            tries_t = 0
            while tries_t < 1:
                tries_t += 1
                
                comb = BoolAnd(f_orig, BoolNot(f_new.clone(True)))
                r = Problem().compute_trace(comb, 'directsat', trace_length=trace_length)
#                print r.sat
                if not r.sat:
                    continue
                trace = r.trace
                t = trace.to_trace_formula()
                
                
                d = Description(specification=f, trace=t) 
                r = Problem().compute_with_description(d, 'directsat')
                if not r.sat:
                    print "f unsat"
                    continue
#                else:
#                    print "f is sat"
    
                d = Description(specification=f_new, trace=t) 
                r = Problem().compute_with_description(d, 'directsat')
                if r.sat:
                    print "f_new sat"
                    continue
#                else:
#                    print "f_new is unsat"
            
                if not check_no_subset_sat(f_new, t, transformations):
                    print "subset sat"
                    continue
                
                return f, f_new, t
