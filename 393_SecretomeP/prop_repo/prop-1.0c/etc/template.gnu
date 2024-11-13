set terminal pbm small color
set output "| _PPM2GIF_ ";
set title "ProP 1.0: predicted propeptide cleavage sites in _NAME_, _PRED_"
set size 1.0,0.6
set xrange [0:_LEN_]
set yrange [0:1.3]
set tics out
set ytics 0,1
set xlabel "Sequence position" 0,0
set ylabel "Propeptide cleavage potential" 0,0
plot '_D_/gr.sp.dat' t"Signal peptide cleavage" w i 1, \
     '_D_/gr.pp.dat' t"Propeptide cleavage" w i 3, \
     0.5 t"Threshold"w l 0
#plot '_D_/gr.sp.dat' t"Signal peptide cleavage" w i 3, \
#     '_D_/gr.pp.dat' t"Propeptide cleavage" w i 8, \
#     0.5 t"Threshold"w l 0
