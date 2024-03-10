#!/bin/bash
sudo fuser -k 6653/tcp
sudo modprobe tcp_bbr

#experiments=("bbr1_sharing" "bbr1_absent_congestion" "bbr1_absent_congestion_loss" "bbr3_sharing" "bbr3_absent_congestion" "bbr3_absent_congestion_loss") 

synch=("bbr1_paper_before" "bbr1_paper_after" "bbr3_paper_before" "bbr3_paper_after" "bbr3_new_before" "bbr3_new_after")
#synch=("bbr3_paper_before" "bbr3_paper_after")

sudo rm -rf synch

for  experiment in "${synch[@]}"
do 
    sudo python3 run_mininet.py configs/synch/"$experiment".conf -d synch/           #  -l 200ms #-s 625000b 
done


for  experiment in "${synch[@]}"
do
    sudo python3 analyze.py -d synch/*_"${experiment}" & 
done

wait

cd synch
sudo chmod -R 777 * 


cd .. 
# cp -r test /media/mihai/WD_BLACK/testRESULTS

#shutdown now