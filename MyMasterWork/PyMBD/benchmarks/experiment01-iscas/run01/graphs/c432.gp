#!/opt/local/bin/gnuplot -persist

# set term pdf monochrome
set terminal epslatex standalone 'ptm' 8 size 10cm,8cm lw 0.75
set output "c432.tex"

numalgs = 16
circuit   = 1

set xtics numalgs+1 format ""
#set ytics 20
set mytics 10
set mxtics 0
set yrange [4e-2 : 5e2]
set xrange [3*(numalgs+1)*(circuit-1) : 3*(numalgs+1)*circuit]

# set title "Test Scenario x (160 Gates)" offset 0, 0.25
set ylabel "\\shortstack{c432.sisc\\\\run-time ($10^y$ sec.)}"  offset 1,0
set xlabel "max. $|\\Delta|$" offset 0,-0.5
set format y "%L"

set logscale y

set grid xtics ytics mxtics mytics ls 4 lw 0.3

set label "1\n"  at graph 0.167, -0.07 center
set label "2\n"  at graph 0.500, -0.07 center
set label "3\n"  at graph 0.833, -0.07 center

set key bmargin Left reverse maxrows 6 samplen -1 width -2
set tmargin 1.3
set rmargin 1
set lmargin 6.5

plot \
	 'data-hsdag-cache-picosat.txt'        using (($1-1)*(numalgs+1) +   1):($2):($3):($4) with errorbars title 'HS-DAG+Cache/PS'     ls 1 lw 2 pt 2 ps 1.1, \
	 'data-hsdag-cache-yices.txt'          using (($1-1)*(numalgs+1) +   2):($2):($3):($4) with errorbars title 'HS-DAG+Cache/Y'      ls 1 lw 2 pt 4 ps 1.1, \
	 'data-hsdag-ci-cache-picosat.txt'     using (($1-1)*(numalgs+1) +   3):($2):($3):($4) with errorbars title 'HS-DAG-CI+Cache/PS'  ls 1 lw 2 pt 5 ps 1.1, \
	 'data-hsdag-ci-cache-yices.txt'       using (($1-1)*(numalgs+1) +   4):($2):($3):($4) with errorbars title 'HS-DAG-CI+Cache/Y'   ls 1 lw 2 pt 14 ps 1.1, \
	 'data-hsdag-ci-picosat.txt'           using (($1-1)*(numalgs+1) +   5):($2):($3):($4) with errorbars title 'HS-DAG-CI/PS'        ls 1 lw 2 pt 6 ps 1.1, \
	 'data-hsdag-ci-yices.txt'             using (($1-1)*(numalgs+1) +   6):($2):($3):($4) with errorbars title 'HS-DAG-CI/Y'         ls 1 lw 2 pt 7 ps 1.1, \
	 'data-hsdag-picosat.txt'              using (($1-1)*(numalgs+1) +   7):($2):($3):($4) with errorbars title 'HS-DAG/PS'           ls 1 lw 2 pt 8 ps 1.1, \
	 'data-hsdag-yices.txt'                using (($1-1)*(numalgs+1) +   8):($2):($3):($4) with errorbars title 'HS-DAG/Y'            ls 1 lw 2 pt 9 ps 1.4, \
	 'data-hst-cache-picosat.txt'          using (($1-1)*(numalgs+1) +   9):($2):($3):($4) with errorbars title 'HST+Cache/PS'        ls 1 lw 2 pt 10 ps 1.1, \
	 'data-hst-cache-yices.txt'            using (($1-1)*(numalgs+1) +  10):($2):($3):($4) with errorbars title 'HST+Cache/Y'         ls 1 lw 2 pt 11 ps 1.4, \
	 'data-hst-ci-cache-picosat.txt'       using (($1-1)*(numalgs+1) +  11):($2):($3):($4) with errorbars title 'HST-CI+Cache/PS'     ls 1 lw 2 pt 12 ps 1.1, \
	 'data-hst-ci-cache-yices.txt'         using (($1-1)*(numalgs+1) +  12):($2):($3):($4) with errorbars title 'HST-CI+Cache/Y'      ls 1 lw 2 pt 13 ps 1.4, \
	 'data-hst-ci-picosat.txt'             using (($1-1)*(numalgs+1) +  13):($2):($3):($4) with errorbars title 'HST-CI/PS'           ls 1 lw 2 pt 17 ps 1.0, \
	 'data-hst-ci-yices.txt'               using (($1-1)*(numalgs+1) +  14):($2):($3):($4) with errorbars title 'HST-CI/Y'            ls 1 lw 2 pt 18 ps 1.0, \
	 'data-hst-picosat.txt'                using (($1-1)*(numalgs+1) +  15):($2):($3):($4) with errorbars title 'HST/PS'              ls 1 lw 2 pt 20 ps 1.0, \
	 'data-hst-yices.txt'                  using (($1-1)*(numalgs+1) +  16):($2):($3):($4) with errorbars title 'HST/Y'               ls 1 lw 2 pt 2 ps 1.1, \
