#!/bin/bash
varying=("bbr3_varying_rtt" "bbr1_varying_rtt")

sudo rm -rf results/varying_rtt

for  experiment in "${varying[@]}"
do 
    sudo python3 run_mininet.py configs/varying_rtt/"$experiment".conf -d results/varying_rtt/           #  -l 200ms #-s 625000b 
done

for  experiment in "${varying[@]}"
do
    sudo python3 analyze.py -d results/varying_rtt/*_"${experiment}" & 
done

wait

# cp -r test /media/mihai/WD_BLACK/testRESULTS

#shutdown now