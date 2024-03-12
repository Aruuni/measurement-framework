sudo fuser -k 6653/tcp
sudo modprobe tcp_bbr
sudo modprobe tcp_cubic


sudo bash bbr_synch_experiment.sh # COMPLETED
sudo bash bbr_single_flow_dynamics.sh
sudo bash bbr_varying_rtt.sh


# sudo rm -r test
# sudo python3 run_mininet.py configs/test.conf -s 50000b -l 25ms
# sudo python3 analyze.py -d test/*_test
# sudo chown -R mihai:mihai test/


sudo chmod -R 777 results
sudo chown -R mihai:mihai results