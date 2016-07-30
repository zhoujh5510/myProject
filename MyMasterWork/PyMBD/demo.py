#!/usr/bin/env python
from pymbd.diagnosis.problem import Problem
from pymbd.benchmark.iscas.oracle import IscasOracle
from pymbd.util.sethelper import write_sets

o = IscasOracle('benchmarks/iscas-data/c17.sisc', [0, 1, 1, 1, 1], [1, 1])
p = Problem()
r = p.compute_with_description(o, 'hsdag-yices', max_card=2)
d = r.get_diagnoses()
d = map(o.numbers_to_gates, d)
print write_sets(d)
print r.get_stats()['total_time']