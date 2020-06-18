# 30 seconds single flow
python run_mininet.py configs/single_flow_30_seconds-bbr.conf
python run_mininet.py configs/single_flow_30_seconds-bbr2.conf

# example bbr
# python run_mininet.py configs/example1.conf
# python run_mininet.py configs/example2.conf
# python run_mininet.py configs/example3.conf

# example bbr2
python run_mininet.py configs/example1-bbr2.conf
python run_mininet.py configs/example2-bbr2.conf
python run_mininet.py configs/example3-bbr2.conf

# example cubic
# python run_mininet.py configs/example1-cubic.conf
# python run_mininet.py configs/example3-cubic.conf

# figure bbr
# python run_mininet.py configs/figure03_single_bbr.conf

# python run_mininet.py configs/figure04_rtt_unfairness_multiple_flows.conf -l 2000ms
# python run_mininet.py configs/figure04_rtt_unfairness_single_flow.conf

# python run_mininet.py configs/figure05_BDP_overestimation.conf -l 500ms

# python run_mininet.py configs/figure08_fair_share.conf -l 100ms

# python run_mininet.py configs/figure14_vegas_bbr_vegas.conf

# python run_mininet.py configs/figure15_add_flow.conf

# figure bbr2
python run_mininet.py configs/figure03_single_bbr2.conf

python run_mininet.py configs/figure04_rtt_unfairness_multiple_flows-bbr2.conf -l 2000ms
python run_mininet.py configs/figure04_rtt_unfairness_single_flow-bbr2.conf

python run_mininet.py configs/figure05_BDP_overestimation-bbr2.conf -l 500ms

python run_mininet.py configs/figure08_fair_share-bbr2-cubic.conf -l 100ms
python run_mininet.py configs/figure08_fair_share-bbr2-bbr.conf -l 100ms

# python run_mininet.py configs/figure14_vegas_bbr_vegas-bbr2.conf

# python run_mininet.py configs/figure15_add_flow-bbr2.conf
