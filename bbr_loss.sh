#!/bin/bash
bbrloss=("bbr3" "bbr1")

sudo rm -rf results/bbrloss/

for  experiment in "${bbrloss[@]}"
do 
    sudo python3 run_mininet.py configs/bbrloss/"$experiment".conf -d results/bbrloss/  -l 25ms  #-s 625000b 
done

for  experiment in "${bbrloss[@]}"
do
    sudo python3 analyze.py -d results/bbrloss/*_"${experiment}" & 
done

wait
