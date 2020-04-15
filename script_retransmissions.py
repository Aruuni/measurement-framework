from helper.csv_writer import read_csv
import glob
import sys
import os
import stat
import numpy as np
import argparse


RTT = 50
CC_ALGO1 = 'cubic'
CC_ALGO2 = 'bbr'
RUN_SH = 'run_retransmissions.sh'
DURATION = 120

def generate_configs(dir):
    # Create directory for config files
    if not os.path.exists(dir):
        os.makedirs(dir)

    # Prepare steps
    steps = np.arange(0.1, 3, 0.1).tolist() + np.arange(3, 10, 0.5).tolist() + np.arange(10, 55, 5).tolist()
    steps = list(map(lambda x: round(x, 1), steps))

    # Write config into folder
    for flow in [CC_ALGO1, CC_ALGO2]:
        config = os.path.join(dir, 'retransmissions_{}.conf'.format(flow)) 
        line = 'host, {}, {}ms, 0.0, {}\n'.format(flow, RTT, DURATION)
        with open(config, 'w') as config_file:
            for counter in range(5):
                config_file.write(line)

    # Open file for commands
    with open(RUN_SH, 'w') as run_file:
        # Write commands to run file
        for flow in [CC_ALGO1, CC_ALGO2]:
            for step in steps:
                run_file.write('python run_mininet.py {}/retransmissions_{}.conf -n "retransmissions_{}_{}" -l {}ms\n'.format(dir, flow, flow, step, step * RTT))

    # Make run file executable
    st = os.stat(RUN_SH)
    os.chmod(RUN_SH, st.st_mode | stat.S_IEXEC)

def analyze(dir):
    t_sync = 25

    output = {}

    for path, dirs, files in os.walk(dir):
        if 'csv_data' not in dirs:
            continue
        try:
            split = path.split('/')[-1].split('_')
            flow = split[-1]
            buffer = split[-2]

        except Exception as e:
            sys.stderr.write('Skipping directory {}\n{}\n'.format(path, e))
            continue

        key = buffer

        if not key in output.keys():
            output[key] = ([], [], [], [])

        if not os.path.exists(os.path.join(path, 'csv_data/retransmissions_interval.csv.gz')):
            sys.stderr.write('Skipping {}\n'.format(path))

        retransmissions = read_csv(os.path.join(path, 'csv_data/retransmissions_interval.csv'), 3)

        # Convert t_sync to absolute time
        t_sync = t_sync + retransmissions[0][0][0]

        packets = 0
        retrans = 0
        packets_half = 0
        retrans_half = 0
        for c in retransmissions:

            start = 0

            for i,t in enumerate(retransmissions[c][0]):
                if t > t_sync:
                    break
                start = i

            packets += sum(retransmissions[c][2][:start])
            packets_half += sum(retransmissions[c][2][start:])

            retrans += sum(retransmissions[c][1][:start])
            retrans_half += sum(retransmissions[c][1][start:])

        # TODO: Change to switch case
        if flow == 'CC_ALGO1':
            output[key][0].append(float(retrans) / packets)
            output[key][1].append(float(retrans_half) / packets_half)
        else:
            output[key][2].append(float(retrans) / packets)
            output[key][3].append(float(retrans_half) / packets_half)

    print('buffersize;bbr;bbrStart;cubic;cubicStart')
    for key in sorted(output.keys(), key=lambda x: float(x)):
        print(';'.join(map(str, [key,
                                 np.mean(output[key][0]),
                                 np.mean(output[key][1]),
                                 np.mean(output[key][2]),
                                 np.mean(output[key][3]),
                                 ])))

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('mode', metavar='MODE',
                        choices=['create', 'analyze'],
                        help='Create configs or analyze data.')
    parser.add_argument('directory', metavar='DIR',
                        help='Output directory for the config files in case of create mode or '
                             'directory of the results for analyze mode.')

    args = parser.parse_args()

    if args.mode == 'create':
        generate_configs(args.directory)

    elif args.mode == 'analyze':
        analyze(args.directory)
