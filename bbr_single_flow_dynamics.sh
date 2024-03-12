#!/bin/bash
singleFlow=("bbr3" "bbr1")

sudo rm -rf results/singleFlow/

for  experiment in "${singleFlow[@]}"
do 
    sudo python3 run_mininet.py configs/single_flow_dynamics/"$experiment".conf -d results/singleFlow/           #  -l 200ms #-s 625000b 
done

for  experiment in "${singleFlow[@]}"
do
    sudo python3 analyze.py -d results/singleFlow/*_"${experiment}" & 
done

wait

# cp -r test /media/mihai/WD_BLACK/testRESULTS

#shutdown now