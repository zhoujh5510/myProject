#!/opt/local/bin/gnuplot -persist
# this settings control total paper and plot size in mm without being influenced 
# by any labels or the legend
PAPER_XSIZE = 75.0
PAPER_YSIZE = 80.0
PLOT_XSIZE  = 60.2
PLOT_YSIZE  = 54.5
MARGIN_TOP  = 1.8
MARGIN_LEFT = 10.5
set macro

set terminal epslatex standalone '' 10 size PAPER_XSIZE/25.4,PAPER_YSIZE/25.4 lw 0.75
set output "experiment02_run01-memory.tex"

set multiplot
set lmargin 0
set rmargin 0
set tmargin 0
set bmargin 0
set size PLOT_XSIZE/PAPER_XSIZE,PLOT_YSIZE/PAPER_YSIZE
set origin MARGIN_LEFT/PAPER_XSIZE,(PAPER_YSIZE-MARGIN_TOP-PLOT_YSIZE)/PAPER_YSIZE

set key at character 0,4 left Left reverse width -3 samplen -1 maxrows 4
# set terminal epslatex 'ptm'
set xlabel "Formula size" offset 0,0.5
set ylabel "max. RSS in $10^y$ MiB" offset 1,0
set logscale x
set logscale y
set xrange [1e0 : 1e3]
set yrange [1e0 : 3000]
set xtics 1, 10, 1000 offset 0, graph 0.01 add ("$10^3$" 1000)
set ytics 1e-4, 10, 1e4 offset graph 0.01, 0 #add ("1" 1, "100" 100, "0.01" 0.01)
set mxtics
set mytics 10
set format y "%L"
# set format x "$10^{%L}$"
# set bmargin 5
set grid xtics ytics ls 4
set grid mxtics mytics ls 4 lw 0.3

cols = "1:($4+$5)"

myline(alg, ti, pt, ls, mint, mstart, le, idx) = "\
    'data-" . alg . ".txt' using ".cols.idx." every 1 title ''  with lines ls ".ls." lw 2, \
    'data-" . alg . ".txt' using ".cols.idx." every ".mint."::".mstart." title '' with \
                points ls ".ls." pt ".pt." ps ".(pt > 7 ? "0.9" : "0.7")." lw 2, \
     NaN title '" . (le eq 'x' ? ti : le) . "' with \
                points ls ".ls." pt ".pt." ps ".(pt > 7 ? "0.9" : "0.7")." lw 2"

lines = "NaN title ''"

lines = lines." ,".myline('hsdag-cache-picosat-1'    , 'HS-DAG+Cache/WFM', 			4, 1, 20, 0, 'x', '')
lines = lines." ,".myline('hsdag-ci-cache-picosat-1' , 'HS-DAG-CI+Cache/WFM', 		5, 1, 20, 1, 'x', '')
lines = lines." ,".myline('hsdag-fm-cache-1'         , 'HS-DAG+Cache/SFM', 			7, 1, 20, 0, 'x', '')
lines = lines." ,".myline('hsdag-ci-fm-cache-1'      , 'HS-DAG-CI+Cache/SFM', 		6, 1, 20, 1, 'x', '')
plot @lines
