#!/bin/bash
trap 'echo Control-C trap caught; exit 1' 2

# ISCAS diagnosis experiment
cd benchmarks/experiment01-iscas/
./compute.py -i iscas-testcases-1.txt -a hst-yices hst-cache-yices hst-ci-yices hst-ci-cache-yices 				   -r run01 -p :10 -m 1,2,3 | tee -a run.log 2>&1
./compute.py -i iscas-testcases-1.txt -a hsdag-yices hsdag-cache-yices hsdag-ci-yices hsdag-ci-cache-yices         -r run01 -p :10 -m 1,2,3 | tee -a run.log 2>&1
./compute.py -i iscas-testcases-1.txt -a hst-picosat hst-cache-picosat hst-ci-picosat hst-ci-cache-picosat         -r run01 -p :10 -m 1,2,3 | tee -a run.log 2>&1
./compute.py -i iscas-testcases-1.txt -a hsdag-picosat hsdag-cache-picosat hsdag-ci-picosat hsdag-ci-cache-picosat -r run01 -p :10 -m 1,2,3 | tee -a run.log 2>&1
cd ../../


# LTL diagnosis experiment
cd benchmarks/experiment02-ltl/
./compute_weak.py   -a hsdag-cache-picosat hsdag-ci-cache-picosat -r run01 -p :100 -m 1 | tee -a run.log 2>&1
./compute_strong.py -a hsdag-fm-cache      hsdag-ci-fm-cache      -r run01 -p :100 -m 1 | tee -a run.log 2>&1
cd ../../


# MHS computation experiment
cd benchmarks/experiment03-mhs/
./compute.py   -a hsdag hst                              -r run01 -p :50 -s 5 | tee -a run.log 2>&1
./compute.py   -a bool-it-h5-stop bool-rec-h1-oldr4      -r run01 -p :50 -s 5 | tee -a run.log 2>&1
./compute.py   -a saths maxsaths                         -r run01 -p :50 -s 5 | tee -a run.log 2>&1
cd ../../



# Plotting the graphs
cd benchmarks/experiment01-iscas/
./plot_graphs.py -r run01
cd ../../

cd benchmarks/experiment02-ltl/
./plot_graphs.py -r run01
cd ../../

cd benchmarks/experiment03-mhs/
./plot_graphs.py -r run01
cd ../../

