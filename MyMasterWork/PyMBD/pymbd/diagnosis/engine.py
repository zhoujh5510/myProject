from ..algorithm.hsdag import Greiner, GreinerO, GreinerFaultModes, GreinerOFaultModes, GreinerN
from ..algorithm.hst import HST, HSTNode, HSTO
from ..algorithm.cardsort import CardSortDiagnosis, MultiCardSortDiagnosis
from ..algorithm.boolean import Boolean
from ..algorithm.maxsat import MaxSatDiagnosis
from ..algorithm.staccato import staccato
from ..algorithm.saths import SatHs
from ..algorithm.maxsaths import MaxSatHs
from ..algorithm.gde import GDE
from ..algorithm.node import Node
from ..diagnosis.description import Description
from ..diagnosis.result import Result
import sys
import time

def merge(opts1, opts2):
    return dict(opts1.items() + opts2.items())

ENGINES = {

        'hst-yices'               : lambda d, o: PyHSTEngine          (d, merge({'sat_solver': 'yices', 'cache':False }, o)), 
        'hst-cache-yices'         : lambda d, o: PyHSTEngine          (d, merge({'sat_solver': 'yices', 'cache':True  }, o)),
        'hst-ci-yices'            : lambda d, o: PyHSTOEngine         (d, merge({'sat_solver': 'yices', 'cache':False }, o)), 
        'hst-ci-cache-yices'      : lambda d, o: PyHSTOEngine         (d, merge({'sat_solver': 'yices', 'cache':True  }, o)),
        'hst-sicf-yices'          : lambda d, o: PyHSTNEngine         (d, merge({'sat_solver': 'yices', 'cache':False }, o)), 
        'hst-sicf-cache-yices'    : lambda d, o: PyHSTNEngine         (d, merge({'sat_solver': 'yices', 'cache':True  }, o)),
        'hsdag-yices'             : lambda d, o: PyHsDagEngine        (d, merge({'sat_solver': 'yices', 'cache':False }, o)), 
        'hsdag-cache-yices'       : lambda d, o: PyHsDagEngine        (d, merge({'sat_solver': 'yices', 'cache':True  }, o)),
        'hsdag-ci-yices'          : lambda d, o: PyHsDagOEngine       (d, merge({'sat_solver': 'yices', 'cache':False }, o)), 
        'hsdag-ci-cache-yices'    : lambda d, o: PyHsDagOEngine       (d, merge({'sat_solver': 'yices', 'cache':True  }, o)),
        'hsdag-sicf-yices'        : lambda d, o: PyHsDagNEngine       (d, merge({'sat_solver': 'yices', 'cache':False }, o)), 
        'hsdag-sicf-cache-yices'  : lambda d, o: PyHsDagNEngine       (d, merge({'sat_solver': 'yices', 'cache':True  }, o)),
        'hsdag-cpp-yices'         : lambda d, o: CppHsDagEngine       (d, merge({'sat_solver': 'yices', 'cache':False }, o)),
        'hsdag-cpp-cache-yices'   : lambda d, o: CppHsDagEngine       (d, merge({'sat_solver': 'yices', 'cache':True  }, o)),
        'maxsat-yices'            : lambda d, o: PyMaxSatEngine       (d, merge({'reuse_sat':True, 'sat_solver':'yices-maxsat'}, o)),
        'multicardsort-scrypto'   : lambda d, o: PyMultiCardSortEngine(d, merge({'reuse_sat':True, 'sat_solver':'scryptominisat', 'relaunch_sat_solver':False}, o)),
        'hst-picosat'             : lambda d, o: PyHSTEngine          (d, merge({'sat_solver': 'picosat', 'cache':False }, o)), 
        'hst-cache-picosat'       : lambda d, o: PyHSTEngine          (d, merge({'sat_solver': 'picosat', 'cache':True  }, o)),
        'hst-ci-picosat'          : lambda d, o: PyHSTOEngine         (d, merge({'sat_solver': 'picosat', 'cache':False }, o)), 
        'hst-ci-cache-picosat'    : lambda d, o: PyHSTOEngine         (d, merge({'sat_solver': 'picosat', 'cache':True  }, o)),
        'hst-sicf-picosat'        : lambda d, o: PyHSTNEngine         (d, merge({'sat_solver': 'picosat', 'cache':False }, o)), 
        'hst-sicf-cache-picosat'  : lambda d, o: PyHSTNEngine         (d, merge({'sat_solver': 'picosat', 'cache':True  }, o)),
        'hsdag-picosat'           : lambda d, o: PyHsDagEngine        (d, merge({'sat_solver': 'picosat', 'cache':False }, o)), 
        'hsdag-cache-picosat'     : lambda d, o: PyHsDagEngine        (d, merge({'sat_solver': 'picosat', 'cache':True  }, o)),
        'hsdag-ci-picosat'        : lambda d, o: PyHsDagOEngine       (d, merge({'sat_solver': 'picosat', 'cache':False }, o)), 
        'hsdag-ci-cache-picosat'  : lambda d, o: PyHsDagOEngine       (d, merge({'sat_solver': 'picosat', 'cache':True  }, o)),
        'hsdag-sicf-picosat'      : lambda d, o: PyHsDagNEngine       (d, merge({'sat_solver': 'picosat', 'cache':False }, o)), 
        'hsdag-sicf-cache-picosat': lambda d, o: PyHsDagNEngine       (d, merge({'sat_solver': 'picosat', 'cache':True  }, o)),
        'hsdag-cpp-picosat'       : lambda d, o: CppHsDagEngine       (d, merge({'sat_solver': 'picosat', 'cache':False }, o)),
        'hsdag-cpp-cache-picosat' : lambda d, o: CppHsDagEngine       (d, merge({'sat_solver': 'picosat', 'cache':True  }, o)),

        'bool-it-h1-stop'         : lambda d, o: PyBooleanIterativeEngine (d, merge({'heuristic':1, 'stopping_optimization':True},  o)),
        'bool-rec-h1-stop'        : lambda d, o: PyBooleanRecursiveEngine (d, merge({'heuristic':1, 'stopping_optimization':True},  o)),
        'bool-it-h4-stop'         : lambda d, o: PyBooleanIterativeEngine (d, merge({'heuristic':4, 'stopping_optimization':True},  o)),
        'bool-rec-h4-stop'        : lambda d, o: PyBooleanRecursiveEngine (d, merge({'heuristic':4, 'stopping_optimization':True},  o)),
        'bool-it-h5-stop'         : lambda d, o: PyBooleanIterativeEngine (d, merge({'heuristic':5, 'stopping_optimization':True},  o)),
        'bool-rec-h5-stop'        : lambda d, o: PyBooleanRecursiveEngine (d, merge({'heuristic':5, 'stopping_optimization':True},  o)),
        'bool-rec-h1-oldr4'       : lambda d, o: PyBooleanRecursiveEngine (d, merge({'heuristic':1, 'old_rule4':True},  o)),
        'bool-rec-h4-oldr4'       : lambda d, o: PyBooleanRecursiveEngine (d, merge({'heuristic':4, 'old_rule4':True},  o)),
        'bool-rec-h5-oldr4'       : lambda d, o: PyBooleanRecursiveEngine (d, merge({'heuristic':5, 'old_rule4':True},  o)),
        'bool-rec-h1-stop-oldr4'  : lambda d, o: PyBooleanRecursiveEngine (d, merge({'heuristic':1, 'stopping_optimization':True, 'old_rule4':True},  o)),
        'bool-rec-h4-stop-oldr4'  : lambda d, o: PyBooleanRecursiveEngine (d, merge({'heuristic':4, 'stopping_optimization':True, 'old_rule4':True},  o)),
        'bool-rec-h5-stop-oldr4'  : lambda d, o: PyBooleanRecursiveEngine (d, merge({'heuristic':5, 'stopping_optimization':True, 'old_rule4':True},  o)),
        'bool-it-h1-oldr4'        : lambda d, o: PyBooleanIterativeEngine (d, merge({'heuristic':1, 'old_rule4':True},  o)),
        'bool-it-h4-oldr4'        : lambda d, o: PyBooleanIterativeEngine (d, merge({'heuristic':4, 'old_rule4':True},  o)),
        'bool-it-h5-oldr4'        : lambda d, o: PyBooleanIterativeEngine (d, merge({'heuristic':5, 'old_rule4':True},  o)),
        'bool-it-h1-stop-oldr4'   : lambda d, o: PyBooleanIterativeEngine (d, merge({'heuristic':1, 'stopping_optimization':True, 'old_rule4':True},  o)),
        'bool-it-h4-stop-oldr4'   : lambda d, o: PyBooleanIterativeEngine (d, merge({'heuristic':4, 'stopping_optimization':True, 'old_rule4':True},  o)),
        'bool-it-h5-stop-oldr4'   : lambda d, o: PyBooleanIterativeEngine (d, merge({'heuristic':5, 'stopping_optimization':True, 'old_rule4':True},  o)),

        'boolean-iterative-c'     : lambda d, o: CppBooleanEngine         (d, o), 
        'staccato'                : lambda d, o: PyStaccatoEngine         (d, o),
        'gde-berge'               : lambda d, o: PyGdeEngine              (d, o), 

        'hsdag-fm'                : lambda d, o: PyHsDagFaultModeEngine   (d, merge({'cache':False}, o)), 
        'hsdag-fm-cache'          : lambda d, o: PyHsDagFaultModeEngine   (d, merge({'cache':True}, o)),
        'hsdag-ci-fm-cache'       : lambda d, o: PyHsDagOFaultModeEngine   (d, merge({'cache':True}, o)),

        'hst'                     : lambda d, o: PyHSTEngine          (d, merge({'cache':False }, o)), 
        'hst-cache'               : lambda d, o: PyHSTEngine          (d, merge({'cache':True  }, o)), 
        'hsdag'                   : lambda d, o: PyHsDagEngine        (d, merge({'cache':False }, o)), 
        'hsdag-cache'             : lambda d, o: PyHsDagEngine        (d, merge({'cache':True  }, o)),

        'saths'                   : lambda d, o: SatHsEngine(d, merge({'sat_solver':'scryptominisat-async'}, o)),
        'maxsaths'                : lambda d, o: MaxSatHsEngine(d, merge({'sat_solver':'yices-maxsat'}, o)),

   }

def hittingsets_from_tree(hstree, card=(1, sys.maxint)):
    hs = set()
    min_card = card[0]
    max_card = card[1]
    if not min_card:
        min_card = 1
    if not max_card:
        max_card = sys.maxint
    if len(hstree.checked_nodes) > 0:
        cardinalities = hstree.checked_nodes.keys()
        for cardinality in xrange(min_card, min(max(cardinalities), max_card)+1):
            if cardinality in cardinalities:
                for node in hstree.checked_nodes[cardinality]:
                    hs.add(node.h)
    return hs

class Engine(object):
    '''
    Encapsules an algorithm that does the actual hitting set computation. 
    This implementation does nothing, derived classes must implement at least 
    the start() method and place a Result object in self.result at the end
    '''

    def __init__(self, description, options):
        '''
        Construct a hitting set computation engine from the problem description. 
        An options hash specific to the algorithm  may be given as second parameter. 
        '''
        self.description = description
        self.options = options
        self.result = None
        self.handle = None
        
    def start(self):
        pass
    
    def get_result(self):
        return self.result
    
    def set_options(self, options):
        self.options.update(options)

class PyHsDagEngine(Engine):
    def __init__(self, description, options):
        super(PyHsDagEngine, self).__init__(description, options)
        o = self.options
        o['min_card'] = o.get('min_card', 1)
        o['max_card'] = o.get('max_card', sys.maxint)
        o['max_time'] = o.get('max_time', None)
        o['prune'] = o.get('prune', True)
        o['cache'] = o.get('cache', False)
        o['debug_pruning'] = o.get('debug_pruning', False)
        
    def start(self):
        o = self.options
        n0 = Node.next_node_number
        t0 = time.time()
        g = Greiner(self.description, self.handle, o)
        self.handle = g.hsdag()
        n1 = Node.next_node_number
        hs = hittingsets_from_tree(self.handle, (o['min_card'], o['max_card']))
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=len(self.handle.nodes()), num_gen_nodes=n1-n0, cache_hits=g.cache_hits, 
                             cache_misses=g.cache_misses,cache_size=len(self.handle.cs_cache), time_map=g.time_map, timeout=g.timeout)


class PyHsDagOEngine(PyHsDagEngine):
    def start(self):
        o = self.options
        n0 = Node.next_node_number
        t0 = time.time()
        g = GreinerO(self.description, self.handle, o)
        self.handle = g.hsdag()
        n1 = Node.next_node_number
        hs = hittingsets_from_tree(self.handle, (o['min_card'], o['max_card']))
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=len(self.handle.nodes()), num_gen_nodes=n1-n0, cache_hits=g.cache_hits, 
                             cache_misses=g.cache_misses,cache_size=len(self.handle.cs_cache), time_map=g.time_map, timeout=g.timeout)
        

class PyHSTEngine(Engine):
    def __init__(self, description, options):
        super(PyHSTEngine, self).__init__(description, options)
        o = self.options
        o['min_card'] = o.get('min_card', 1)
        o['max_card'] = o.get('max_card', sys.maxint)
        o['max_time'] = o.get('max_time', None)
        o['prune'] = o.get('prune', True)
        o['cache'] = o.get('cache', False)
        
    def start(self):
        o = self.options
        n0 = HSTNode.next_node_number
        t0 = time.time()
        h = HST(self.description, self.handle, o)
        self.handle = h.hst()
        hs = hittingsets_from_tree(self.handle, (o['min_card'], o['max_card']))
        n1 = HSTNode.next_node_number
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=self.handle.num_nodes(), num_gen_nodes=n1-n0, cache_hits=h.cache_hits, 
                             cache_misses=h.cache_misses,cache_size=len(self.handle.cs_cache))
                             

class PyHSTOEngine(PyHSTEngine):
    def start(self):
        o = self.options
        n0 = HSTNode.next_node_number
        t0 = time.time()
        h = HSTO(self.description, self.handle, o)
        self.handle = h.hst()
        hs = hittingsets_from_tree(self.handle, (o['min_card'], o['max_card']))
        n1 = HSTNode.next_node_number
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=self.handle.num_nodes(), num_gen_nodes=n1-n0, cache_hits=h.cache_hits, 
                             cache_misses=h.cache_misses,cache_size=len(self.handle.cs_cache))


class CppHsDagEngine(PyHsDagEngine):
    def start(self):
        import os
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'cresources', 'src'))
        import c_algorithm
        o = self.options
        o['max_time'] = o['max_time'] or 0.0 # can't convert None to double
        c_algorithm.set_problem_size(self.description.get_num_components())
        description = self.description
        hsdag = c_algorithm.HsDag()
        if self.handle:
            n0 = self.handle.next_node_id
        else:
            n0 = 0
        if type(self.description) == Description:
            description = c_algorithm.Description(description.get_conflict_sets(), False) # do not sort again, just use the order from the python Description
            self.handle = hsdag.hsdag_cpp(description, o['max_card'], self.handle, o['max_time'], o['prune'], o['cache'])
        else:
            self.handle = hsdag.hsdag_py(description, o['max_card'], self.handle, o['max_time'], o['prune'], o['cache'])
        n1 = self.handle.next_node_id
        hs = hsdag.hittingsets_from_tree(self.handle, (1, o['max_card'])) # this uses the C++ version of hittingsets_from_tree !!
        self.result = Result(hs, total_time=hsdag.get_calculation_time(), tp_time_comp=description.get_comp_time(), tp_time_check=description.get_check_time(), 
                             num_tpcalls_comp=description.get_comp_calls(), num_tpcalls_check=description.get_check_calls(), num_nodes=self.handle.get_num_nodes(), 
                             num_gen_nodes=n1-n0)


class PyMaxSatEngine(Engine):
    def __init__(self, description, options):
        super(PyMaxSatEngine, self).__init__(description, options)
        
    def start(self):
        t0 = time.time()
        m = MaxSatDiagnosis(self.description, self.options.get('previous_solutions', None), **self.options)
        hs = m.start()
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=0, num_gen_nodes=0, cache_hits=0, 
                             cache_misses=0, cache_size=0, time_map=m.time_map, timeout=m.timeout)

class PyCardSortEngine(Engine):
    def __init__(self, description, options):
        super(PyCardSortEngine, self).__init__(description, options)
        
    def start(self):
        t0 = time.time()
        m = CardSortDiagnosis(self.description, self.options.get('previous_solutions', None), **self.options)
        hs = m.start()
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=0, num_gen_nodes=0, cache_hits=0, 
                             cache_misses=0, cache_size=0, time_map=m.time_map, timeout=m.timeout)

class PyMultiCardSortEngine(Engine):
    def __init__(self, description, options):
        super(PyMultiCardSortEngine, self).__init__(description, options)
        
    def start(self):
        t0 = time.time()
        m = MultiCardSortDiagnosis(self.description, self.options.get('previous_solutions', None), **self.options)
        self.handle = m
        hs = m.start()
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=0, num_gen_nodes=0, cache_hits=0, 
                             cache_misses=0, cache_size=0, time_map=m.time_map, timeout=m.timeout)


class PyBooleanEngine(Engine):
    def __init__(self, description, options):
        super(PyBooleanEngine, self).__init__(description, options)
        o = self.options
        o['min_card'] = o.get('min_card', 1)
        o['max_card'] = o.get('max_card', sys.maxint)
        o['max_time'] = o.get('max_time', None)
        self.boolean = Boolean(self.description, options)
        
    def start(self):
        pass

class PyBooleanIterativeEngine(PyBooleanEngine):
    def start(self):
        o = self.options
        t0 = time.time()
        self.handle, hs = self.boolean.boolean_iterative()
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=0, num_gen_nodes=0, num_h_calls=self.boolean.num_h_calls)
        
class PyBooleanRecursiveEngine(PyBooleanEngine):
    def start(self):
        o = self.options
        t0 = time.time()
        hs = self.boolean.boolean_recursive()
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=0, num_gen_nodes=0, num_h_calls=self.boolean.num_h_calls)

class CppBooleanEngine(PyBooleanEngine):
    def start(self):
        import c_algorithm
        o = self.options
        o['max_time'] = o['max_time'] or 0.0 # can't convert None to double
        c_algorithm.set_problem_size(self.description.get_num_components())
        description = self.description
        if type(self.description) == Description:
            description = c_algorithm.Description(description.get_conflict_sets(), False) # do not sort again, just use the order from the python Description
        boolean = c_algorithm.Boolean()
        self.handle = boolean.boolean_iterative(description, o['max_card'], self.handle, o['max_time'])
        hs = self.handle.get_hitting_sets(o['min_card'], o['max_card'])
        self.result = Result(hs, total_time=boolean.get_calculation_time(), tp_time_check=0, tp_time_comp=0, num_tpcalls_check=0, num_tpcalls_comp=0, 
                             num_nodes=0, num_gen_nodes=0)


class PyGdeEngine(Engine):
    def __init__(self, description, options):
        super(PyGdeNewEngine, self).__init__(description, options)
        o = self.options
        o['min_card'] = o.get('min_card', 1)
        o['max_card'] = o.get('max_card', sys.maxint)
        o['max_time'] = o.get('max_time', None)
        
    def start(self):
        o = self.options
        t0 = time.time()
        g = GDE(self.description, None, o)
        hs = g.start()
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=0, num_gen_nodes=0, cache_hits=0, cache_misses=0,cache_size=0)

class PyStaccatoEngine(Engine):
    def start(self):
        t0 = time.time()
        hs = staccato(self.description)
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=0, num_gen_nodes=0)


class PyHsDagFaultModeEngine(PyHsDagEngine):
    def start(self):
        o = self.options
        n0 = Node.next_node_number
        t0 = time.time()
        g = GreinerFaultModes(self.description, self.handle, o)
        self.handle = g.hsdag()
        n1 = Node.next_node_number
        hs = hittingsets_from_tree(self.handle, (o['min_card'], o['max_card']))
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=len(self.handle.nodes()), num_gen_nodes=n1-n0, cache_hits=g.cache_hits, 
                             cache_misses=g.cache_misses, cache_size=len(self.handle.cs_cache), cache_hits_fm=g.cache_hits_fm, time_map=g.time_map, 
                             timeout=g.timeout)

class PyHsDagOFaultModeEngine(PyHsDagEngine):
    def start(self):
        o = self.options
        n0 = Node.next_node_number
        t0 = time.time()
        g = GreinerOFaultModes(self.description, self.handle, o)
        self.handle = g.hsdag()
        n1 = Node.next_node_number
        hs = hittingsets_from_tree(self.handle, (o['min_card'], o['max_card']))
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=len(self.handle.nodes()), num_gen_nodes=n1-n0, cache_hits=g.cache_hits, 
                             cache_misses=g.cache_misses, cache_size=len(self.handle.cs_cache), cache_hits_fm=g.cache_hits_fm, time_map=g.time_map, 
                             timeout=g.timeout)

class SatHsEngine(Engine):
    def __init__(self, description, options):
        super(SatHsEngine, self).__init__(description, options)
        
    def start(self):
        t0 = time.time()
        m = SatHs(self.description, **self.options)
        self.handle = m
        hs = m.start()
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=0, num_gen_nodes=0, cache_hits=0, 
                             cache_misses=0, cache_size=0, time_map=m.time_map, timeout=m.timeout)
        
class MaxSatHsEngine(Engine):
    def __init__(self, description, options):
        super(MaxSatHsEngine, self).__init__(description, options)
        
    def start(self):
        t0 = time.time()
        m = MaxSatHs(self.description, **self.options)
        self.handle = m
        hs = m.start()
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=0, num_gen_nodes=0, cache_hits=0, 
                             cache_misses=0, cache_size=0, time_map=m.time_map, timeout=m.timeout)
        
class PyHSTNEngine(PyHSTEngine):
    def start(self):
        o = self.options
        n0 = HSTNode.next_node_number
        t0 = time.time()
        h = HSTN(self.description, self.handle, o)
        self.handle = h.hst()
        hs = hittingsets_from_tree(self.handle, (o['min_card'], o['max_card']))
        n1 = HSTNode.next_node_number
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=self.handle.num_nodes(), num_gen_nodes=n1-n0, cache_hits=h.cache_hits, 
                             cache_misses=h.cache_misses,cache_size=len(self.handle.cs_cache))

class PyHsDagNEngine(PyHsDagEngine):
    def start(self):
        o = self.options
        n0 = Node.next_node_number
        t0 = time.time()
        g = GreinerN(self.description, self.handle, o)
        self.handle = g.hsdag()
        n1 = Node.next_node_number
        hs = hittingsets_from_tree(self.handle, (o['min_card'], o['max_card']))
        t1 = time.time()
        d = self.description
        self.result = Result(hs, total_time=t1-t0, tp_time_check=d.get_check_time(), tp_time_comp=d.get_comp_time(), num_tpcalls_check=d.get_check_calls(), 
                             num_tpcalls_comp=d.get_comp_calls(), num_nodes=len(self.handle.nodes()), num_gen_nodes=n1-n0, cache_hits=g.cache_hits, 
                             cache_misses=g.cache_misses,cache_size=len(self.handle.cs_cache), time_map=g.time_map, timeout=g.timeout)

