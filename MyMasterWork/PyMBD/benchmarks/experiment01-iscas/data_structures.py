from pymbd.util.struct import makestruct
from pymbd.benchmark.csv_framework import CSVObject
import os


class Problem(CSVObject):
    file = "problems.txt"
    fields =     [ 'pid', 'ngates', 'nmutations', 'ncomp', 'ncs', 'neffcs', 'file'  ]
    converters = [ int,   int,      int,           int,     int,   int,     str     ]
    
class Result(CSVObject):
    
    has_header =  True
    
    fields     =  ['experiment', 'run_id', 'datetime', 'pid', 'algorithm', 'ncs', 'ncomp', 'neffcs', 'max_card' ]
    formats    =  ['%s',         '%s',     '%s',       '%d',  '%s',        '%d',  '%d',    '%d',     '%d'       ]
    converters =  [str,          str,      str,        int,   str,         int,   int,     int,      int        ]
    
    fields     += ['exectime', 'tp_time_check', 'tp_time_comp', 'nnodes', 'ngen_nodes', 'ntp_check_calls', 'ntp_comp_calls' ] 
    formats    += ['%.16f',    '%.16f',         '%.16f',        '%d',     '%d',         '%d',              '%d'             ]
    converters += [float,      float,           float,          int,      int,          int,               int              ]        
        
    fields     += ['nmhs', 'mhshash', 'max_rss', 'ngates', 'nmutations', 'timeout', 'memout', 'nh_calls', 'file', 'tp_max_rss']
    formats    += ['%d',   '%s',      '%7.2f',   '%d',     '%d'        , '%s'     , '%s'    , '%d'      , '%s'  , '%7.2f'     ]
    converters += [int,    str,       float,     int,      int         , bool     , bool    , int       , str   ,  float      ]
 
    fields     += ['cache_hits', 'cache_misses', 'cache_size']
    formats    += ['%d'        , '%d'          , '%d'        ]
    converters += [int         , int           , int         ]
        
    def append(cls, **args):
        if args['algorithm'] is None or args['algorithm'] == "":
            raise "Cannot save Result to file if no algorithm given"
        filename = "results-%s.txt" % args['algorithm']
        if not os.path.exists(filename):
            with open(filename, 'a') as file:
                file.write("\t".join(cls.fields) + "\n")
        with open(filename, 'a') as file:
            formatstr = "\t".join(cls.formats)
            values = tuple(map(lambda f: args[f], cls.fields))
            file.write((formatstr % values) + "\n")
    append = classmethod(append)

    def get_total_time(self):
        if self.exectime == 0 and self.max_rss >= 2500:
            return 300.0
        return self.exectime + self.tp_time_comp + self.tp_time_check

    total_time = property(get_total_time)
    
Task = makestruct('Task', 'card algorithm pid sample')

