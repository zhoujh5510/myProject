from pymbd.benchmark.ltl.ltlparser.ast import BoolNot, Trace, TraceStem, TraceStep, TraceLoop
from ..engine import Engine, ENGINES
from ..result import Result
from pymbd.benchmark.ltl.encoding.direct_encoding import DirectEncoding, DirectEncodingVar2

merge = lambda o1, o2: dict(o1.items() + o2.items())

ENGINES['directsat']                 = lambda d, o: DirectSatEngine (d, o) 
ENGINES['directsat-core']            = lambda d, o: DirectSatEngine (d, merge({'calculate_unsat_core': True, },o)) 
ENGINES['directsat-not']             = lambda d, o: DirectSatEngine (d, merge({'invert_formula': True, },o)) 
ENGINES['directsat-core-not']        = lambda d, o: DirectSatEngine (d, merge({'invert_formula': True,'calculate_unsat_core': True},o)) 
ENGINES['directsat-comb']            = lambda d, o: DirectSatEngine (d, merge({'combined': True},o))
ENGINES['directsat-faults']          = lambda d, o: DirectSatEngine (d, merge({'calculate_unsat_core': True, 'fault_mode_opts':{'all':True}},o))

ENGINES['directsat-minisat']         = lambda d, o: DirectSatEngine (d, merge({'sat_solver':'minisat'}, o)) 
ENGINES['directsat-minisat-not']     = lambda d, o: DirectSatEngine (d, merge({'invert_formula': True, 'sat_solver':'minisat'}, o)) 
ENGINES['directsat-minisat-comb']    = lambda d, o: DirectSatEngine (d, merge({'combined': True, 'sat_solver':'minisat'}, o)) 

ENGINES['directsat-minisatold']      = lambda d, o: DirectSatEngine (d, merge({'sat_solver':'minisat-old'}, o)) 
ENGINES['directsat-minisatold-not']  = lambda d, o: DirectSatEngine (d, merge({'invert_formula': True, 'sat_solver':'minisat-old'}, o)) 
ENGINES['directsat-minisatold-comb'] = lambda d, o: DirectSatEngine (d, merge({'combined': True, 'sat_solver':'minisat-old'}, o)) 

ENGINES['directsat-weak']            = lambda d, o: DirectSatEngine (d, merge({'calculate_unsat_core': False, 'fault_mode_opts':{'ab_predicates':True}},o))
ENGINES['directsat-strong']          = lambda d, o: DirectSatEngine (d, merge({'calculate_unsat_core': False, 'fault_mode_opts':{'all':True}},o))

ENGINES['directsat-weak-core']       = lambda d, o: DirectSatEngine (d, merge({'calculate_unsat_core': True, 'fault_mode_opts':{'ab_predicates':True}},o))
ENGINES['directsat-strong-core']     = lambda d, o: DirectSatEngine (d, merge({'calculate_unsat_core': True, 'fault_mode_opts':{'all':True}},o))

ENGINES['directsat-z3dimacs']        = lambda d, o: DirectSatEngine (d, merge({'sat_solver':'z3-dimacs'}, o)) 
ENGINES['directsat-z3clause']        = lambda d, o: DirectSatEngine (d, merge({'sat_solver':'z3-clause'}, o)) 

class DirectSatEngine(Engine):

    """
    Engine registering our direct SAT encoding with various options. 
    """

    def __init__(self, description, options):
        super(DirectSatEngine, self).__init__(description, options)
        self.handle = None
        self.options['calculate_unsat_core'] = self.options.get('calculate_unsat_core',False)
        self.options['invert_formula'] = self.options.get('invert_formula',False)
        self.options['combined'] = self.options.get('combined',False)
        self.options['get_trace'] = self.options.get('get_trace', False)
        self.options['fault_mode_opts'] = self.options.get('fault_mode_opts', {})
        self.options['sat_solver'] = self.options.get('sat_solver', 'picosat')
        self.options['exclude_traces'] = self.options.get('exclude_traces', set())
        self.options['encoding_variant_class'] = self.options.get('encoding_variant_class', DirectEncoding)
        
    def start(self):
        
        if not self.description.specification:
            raise Exception("Must supply formula to check")
        
        s = self.description.specification
        if self.options['invert_formula'] == True:
            s = BoolNot(s)
         
        if not self.description.trace:
            if self.options.get('trace_length',None):
                length = self.options['trace_length']
            else:
                length = (10,5)
            t = Trace(TraceStem(*map(lambda i: TraceStep(), xrange(length[1]))), TraceLoop(*map(lambda i: TraceStep(), xrange(length[0]-length[1]))))
            d = self.options['encoding_variant_class'](self.description.specification, t, self.options['exclude_traces'],)
            get_valuation = True
        else :
            d = self.options['encoding_variant_class'](s, self.description.trace, self.options['exclude_traces'], **self.options['fault_mode_opts'])
            get_valuation = False
        
        get_valuation = get_valuation or self.options['get_trace']
        
        o = self.options
        sat = d.check(calculate_unsat_core=o['calculate_unsat_core'], trace_for_unsat=o['combined'], get_valuation=get_valuation, sat_solver=o['sat_solver'])
        self.handle = d
        
        if get_valuation:
            trace = d.get_trace(d.output)
#            d.print_sat_trace()
        else:
            trace = None
        self.result = Result(sat, trace=trace, **d.stats)
        
        return self.result
