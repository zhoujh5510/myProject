#!/opt/local/bin/gnuplot -persist
# this settings control total paper and plot size in mm without being influenced 
# by any labels or the legend
PAPER_XSIZE = 75.0
PAPER_YSIZE = 73.0
PLOT_XSIZE  = 60.2
PLOT_YSIZE  = 54.5
MARGIN_TOP  = 1.8
MARGIN_LEFT = 10.5
set macro

set terminal epslatex standalone '' 10 size PAPER_XSIZE/25.4,PAPER_YSIZE/25.4 lw 0.75
set output "experiment01_run01-time.tex"

set multiplot
set lmargin 0
set rmargin 0
set tmargin 0
set bmargin 0
set size PLOT_XSIZE/PAPER_XSIZE,PLOT_YSIZE/PAPER_YSIZE
set origin MARGIN_LEFT/PAPER_XSIZE,(PAPER_YSIZE-MARGIN_TOP-PLOT_YSIZE)/PAPER_YSIZE

set key at character 0,2 left Left reverse width -3 samplen -1 maxrows 2
# unset key
# set terminal epslatex 'ptm'

set xlabel "$|$COMP$|$" offset 0,0.5
set ylabel "run-time ($10^y$ sec.)" offset 1,0
set logscale x
set logscale y
set xrange [1e0 : 1e3]
set yrange [1e-5 : 1e3]
set xtics 1, 10, 1000 offset 0, graph 0.01 add ("$10^3$" 1000)
set ytics 1e-4, 10, 1e4 offset graph 0.01, 0 #add ("1" 1, "100" 100, "0.01" 0.01)
set mxtics
set mytics 10
set format y "%L"
# set format x "$10^{%L}$"
# set tmargin 0.5
# set rmargin 2
# set lmargin 5
# set bmargin 5
set grid xtics ytics ls 4
set grid mxtics mytics ls 4 lw 0.3

cols = "1:2"

myline(alg, ti, pt, ls, mint, mstart, le, idx) = "\
    'data-" . alg . ".txt' using ".cols.idx." every 1 title ''  with lines ls ".ls." lw 2, \
    'data-" . alg . ".txt' using ".cols.idx." every ".mint."::".mstart." title '' with \
                points ls ".ls." pt ".pt." ps ".(pt > 7 ? "0.9" : "0.7")." lw 2, \
     NaN title '" . (le eq 'x' ? ti : le) . "' with \
                points ls ".ls." pt ".pt." ps ".(pt > 7 ? "0.9" : "0.7")." lw 2"

lines = "NaN title ''"

lines = lines." ,".myline('hst', 				'HST', 			4, 1, 20, 1, 'x', '')
lines = lines." ,".myline('hsdag', 				'HS-DAG', 		5, 1, 20, 2, 'x', '')
lines = lines." ,".myline('bool-it-h5-stop', 	'Bool-It.-Opt', 6, 1, 20, 1, 'x', '')
lines = lines." ,".myline('saths', 				'HS-SAT', 		7, 1, 20, 2, 'x', '')
lines = lines." ,".myline('maxsaths', 			'HS-MaxSAT', 	8, 1, 20, 1, 'x', '')
lines = lines." ,".myline('bool-rec-h1-oldr4', 	'Bool-Rec.', 	9, 1, 20, 2, 'x', '')
plot @lines
