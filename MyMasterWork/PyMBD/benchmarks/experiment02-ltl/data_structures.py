from pymbd.util.struct import makestruct
from pymbd.benchmark.csv_framework import CSVObject
import csv
import os
    
class Problem(CSVObject):
    file = "problems.txt"
    fields =     [ 'pid', 'specid', 'specsize', 'specnumvars', 'tracesize', 'tracestemsize', 'num_faults' ]
    converters = [ int,   int,      int,        int,           int,         int            , int          ]
    
class Result(CSVObject):
    
    has_header =  True
    
    fields     =  ['experiment', 'run_id', 'datetime', 'pid', 'algorithm', 'specsize', 'specnumvars', 'tracesize', 'tracestemsize' ]
    formats    =  ['%s',         '%s',     '%s',       '%d',  '%s',        '%d',       '%d',          '%d',         '%d'           ]
    converters =  [str,          str,      str,        int,   str,         int,         int,           int,         int            ]
    
    fields     += ['enc_time_spec', 'enc_time_trace', 'enc_solver_time', 'enc_total_time', 'enc_num_clauses', 'enc_num_vars', 'found'] 
    formats    += ['%.16f',         '%.16f',          '%.16f',           '%.16f',          '%d' ,              '%d'         , '%d'   ]
    converters += [float,            float,            float,            float,            int  ,             int           , bool   ]        
        
    fields     += ['first_timestamp', 'tp_time_check', 'total_time', 'num_tpcalls_check', 'num_gen_nodes', 'cache_hits_fm', 'num_nodes']
    formats    += ['%.16f'          , '%.16f'        , '%.16f'     , '%d'               , '%d'           , '%d'           , '%d'       ]
    converters += [float            , float          , float       , int                , int            , int            , int        ]
    
    fields     += ['tp_time_comp', 'cache_misses', 'cache_hits', 'cache_size', 'num_hs', 'num_hs1', 'num_hs2', 'num_hs3', 'num_tpcalls_comp']
    formats    += ['%.16f'       , '%d'          , '%d'        , '%d'        , '%d'    , '%d'     , '%d'     , '%d'     , '%d'              ]
    converters += [float         , int           , int         , int         , int     , int      , int      , int      , int               ]
    
    fields     += ['timeout', 'memout', 'max_rss', 'sat_max_rss', 'num_rss_polls', 'num_faults', 'max_card']
    formats    += ['%d'     , '%d'    , '%.2f'   , '%.2f'       , '%d'           , '%d'        , '%d'      ]
    converters += [int      , int     , float    , float        , int            , int         , int       ]
    
        
    def append(cls, **args):
        if args['algorithm'] is None or args['algorithm'] == "":
            raise "Cannot save Result to file if no algorithm given"
        filename = "results-%s.txt" % args['algorithm']
        if not os.path.exists(filename):
            with open(filename, 'a') as file:
                file.write("\t".join(cls.fields) + "\n")
        with open(filename, 'a') as file:
            formatstr = "\t".join(cls.formats)
            values = tuple(map(lambda f: args.get(f, cls.converters[cls.fields.index(f)]()), cls.fields))
            file.write((formatstr % values) + "\n")
    append = classmethod(append)
    
Task = makestruct('Task', 'algorithm pid sample card')

