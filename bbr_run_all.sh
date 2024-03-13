sudo fuser -k 6653/tcp
sudo modprobe tcp_bbr
sudo modprobe tcp_cubic


sudo bash bbr_synch_experiment.sh
sudo bash bbr_single_flow_dynamics.sh
sudo bash bbr_varying_rtt.sh
sudo bash bbr_bbr3Vbbr1.sh
sudo bash bbr_loss.sh


# for testing 

# sudo rm -r test
# sudo python3 run_mininet.py configs/test.conf  -l 5000ms
# sudo python3 analyze.py -d test/*_test
# sudo chown -R mihai:mihai test/


# sudo chown -R mihai:mihai results

# cp -r results  /media/

# shutdown now