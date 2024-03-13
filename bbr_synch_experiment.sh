#!/bin/bash
synch=("bbr1_paper_before" "bbr1_paper_after" "bbr3_paper_before" "bbr3_paper_after" "bbr3_new_before" "bbr3_new_after")

sudo rm -rf results/synch

for  experiment in "${synch[@]}"
do 
    sudo python3 run_mininet.py configs/synch/"$experiment".conf -d results/synch/     #    -l 20ms #-s 625000b 
done

for  experiment in "${synch[@]}"
do
    sudo python3 analyze.py -d results/synch/*_"${experiment}" & 
done

wait