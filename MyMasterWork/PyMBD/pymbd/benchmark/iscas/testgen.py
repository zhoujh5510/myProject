from gate import Gate
from net import Net
from parser import SimpleParser
import logging
import random

log = logging.getLogger(__name__)

GATE_MUTATION = {
    'nand' : 'nor',
    'nor'  : 'nand',
    'not'  : 'buff',
    'and'  : 'nand',
    'or'   : 'and',
    'xor'  : 'or',
    'xnor' : 'nor',
    'buff' : 'not'
}

def generate_iscas_faults(file, num_mutated_gates):

    net = Net(*SimpleParser(open(file)).parse())
    net.generate_random_inputs()
    net.calculate_outputs()
    original_outputs = dict(net.outputs)
    tries = 0
    while tries < 100:
        gates = random.sample(net.gates.values(), num_mutated_gates)
        mutated_gates = []
        tries += 1        
        for g in gates:
            m = Gate(*g)
            m.type = GATE_MUTATION[m.type]
            mutated_gates.append(m)
        
        original_gates = net.mutate_net(mutated_gates)
        net.reset_outputs()
        net.calculate_outputs()
        net.mutate_net(original_gates)
        if net.outputs != original_outputs:
            return [file, net.input_values_compact(), mutated_gates]
    print "Failed to generate fault for " + file + " within 100 tries."
    net.finished()
    
    
def generate_independent_faults(file, num_gates_to_mutate, exclude_gates=[]):
    net = Net(*SimpleParser(open(file)).parse())
    if len(net.outputs) < num_gates_to_mutate:
        net.finished()
        raise Exception("Cannot create %d independent mutations for net with %d outputs" % (num_gates_to_mutate, len(net.outputs)))
    try_num = 1
    log.info("Trying to generate %d independent fault(s) for %s" % (num_gates_to_mutate, file))
    while try_num < 2*(2**len(net.inputs)):                                 # try about two times the number of possible input combinations
        try_num += 1
        net.generate_random_inputs()
        log.debug("=== Trying input %s" % net.inputs)
        net.reset_outputs()                                                 # unconstrain all outputs at the beginning
        net.calculate_outputs()
        previous_outputs = dict(net.outputs)
        log.debug("Original Outputs: %s" % previous_outputs)
        net.reset_outputs()
        gates_to_try = filter(lambda g: g.output not in exclude_gates, net.gates.values())
        mutated_gates = []
        immutable_outputs = set()
        while len(mutated_gates) < num_gates_to_mutate:
            while gates_to_try:
                log.debug("Previous output: %s" % previous_outputs)
                random.shuffle(gates_to_try)
                gate = gates_to_try.pop()
                mutated_gate = Gate(*gate)
                mutated_gate.type = GATE_MUTATION[mutated_gate.type]
                log.debug("Mutating %s to %s" % (gate, mutated_gate))
                net.mutate_net([mutated_gate])
                if not net.calculate_outputs():
                    log.debug("Unsatisfiable, undoing mutation.")
                    net.mutate_net([gate])                                  # restore original gate
                    break
                new_outputs = dict(net.outputs)
                log.debug("New output: %s" % new_outputs)
                changed_outputs   = set([g for g in new_outputs if new_outputs[g] != previous_outputs[g]])
                if changed_outputs:
                    log.debug("found mutation")
                    immutable_outputs |= changed_outputs
                    log.debug("Immutable outputs: %s" % immutable_outputs)
                    mutated_gates.append(mutated_gate)
                    previous_outputs = new_outputs
                    for o in net.outputs:                                   # unconstrain all outputs that didn't change
                        if o not in immutable_outputs:
                            net.outputs[o] = None
                    break
                else: 
                    log.debug("undoing mutation, trying next")
                    net.mutate_net([gate])
                    for o in net.outputs:                                   # unconstrain all outputs that didn't change (in the last step)
                        if o not in immutable_outputs:
                            net.outputs[o] = None
            # end while gates_to_try
            if not gates_to_try and len(mutated_gates) < num_gates_to_mutate:
                log.debug("no more gates to try :(")
                break
        # end while len(mutated_gates) < num_gates_to_mutate:
        if not len(mutated_gates) < num_gates_to_mutate:
            break
        
    net.finished()
    # end while try_num < 2*(2**len(net.inputs)):
    if len(mutated_gates) < num_gates_to_mutate:
        return None
    return [file, net.input_values_compact(), mutated_gates]





#logging.basicConfig(level=logging.DEBUG)
        
#for file in glob('../../iscas-data/*.sisc'):
#    print generate_iscas_faults(file, 1)
    
#print generate_independent_faults('../../iscas-data/c1908.sisc', 3)
