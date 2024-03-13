#!/bin/bash
bbrvbbr3=("bbr3vs1")

sudo rm -rf results/singleFlow/

for  experiment in "${bbrvbbr3[@]}"
do 
    sudo python3 run_mininet.py configs/bbr3vs1/"$experiment".conf -d results/bbr3vs1/           #  -l 200ms #-s 625000b 
done

for  experiment in "${bbrvbbr3[@]}"
do
    sudo python3 analyze.py -d results/bbr3vs1/*_"${experiment}" & 
done

wait



#shutdown now