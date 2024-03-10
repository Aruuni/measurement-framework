from helper.csv_writer import read_csv
import glob
import sys
import os
import stat
import numpy as np
import argparse
import csv


RTT = 50
TEST = 'retransmissions'
RUN_SH = 'run_' + TEST + '.sh'
CC_ALGO1 = 'cubic'
CC_ALGO2 = 'bbr'
CC_ALGO3 = 'bbr2'
DURATION = 120

def generate_configs(dir):
    # Create directory for config files
    if not os.path.exists(dir):
        os.makedirs(dir)

    # Prepare steps
    steps = np.arange(0.1, 3, 0.1).tolist() + np.arange(3, 10, 0.5).tolist() + np.arange(10, 55, 5).tolist()
    steps = list(map(lambda x: round(x, 1), steps))

    # Write config into folder
    for flow_type in [CC_ALGO1, CC_ALGO2]:
        config = os.path.join(dir, 'retransmissions_{}.conf'.format(flow_type)) 
        line = 'host, {}, {}ms, 0.0, {}\n'.format(flow_type, RTT, DURATION)
        with open(config, 'w') as config_file:
            for i in range(5):
                config_file.write(line)

    # Open file for commands
    with open(RUN_SH, 'w') as run_file:
        # Write commands to run file
        for flow_type in [CC_ALGO1, CC_ALGO2]:
            for step in steps:
                run_file.write('python run_mininet.py {}/retransmissions_{}.conf -n \
                    "retransmissions_{}_{}" -l {}ms\n'.format(dir, flow_type, flow_type, step, step * RTT))

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
            buffer = split[-1]
            flow_type = split[-2]

        except Exception as e:
            sys.stderr.write('Skipping directory {}\n{}\n'.format(path, e))
            continue

        key = buffer

        if not key in output.keys():
            output[key] = ([], [], [], [], [], [])

        if not os.path.exists(os.path.join(path, 'csv_data', 'retransmissions_interval.csv.gz')):
            sys.stderr.write('Skipping {}\n'.format(path))

        retransmissions = read_csv(os.path.join(path, 'csv_data', 'retransmissions_interval.csv'), 3)

        # Convert t_sync to absolute time
        t_sync = 25
        t_sync = t_sync + retransmissions[0][0][0]

        packets = 0
        retrans = 0
        packets_half = 0
        retrans_half = 0

        start = 0
        for i,t in enumerate(retransmissions[0][0]):
            if t > t_sync:
                break
            start = i

        for flow_num in retransmissions:

            packets += sum(retransmissions[flow_num][2][:start])
            packets_half += sum(retransmissions[flow_num][2][start:])

            retrans += sum(retransmissions[flow_num][1][:start])
            retrans_half += sum(retransmissions[flow_num][1][start:])

        if flow_type == CC_ALGO1:
            output[key][0].append(float(retrans) / packets)
            output[key][1].append(float(retrans_half) / packets_half)
        elif flow_type == CC_ALGO2:
            output[key][2].append(float(retrans) / packets)
            output[key][3].append(float(retrans_half) / packets_half)
        elif flow_type == CC_ALGO3:
            output[key][4].append(float(retrans) / packets)
            output[key][5].append(float(retrans_half) / packets_half)

    result_file_name = 'result_{}.csv'.format(TEST)
    with open(result_file_name, 'wb') as result_file:
        result_writer = csv.writer(result_file, delimiter=';')

        if 'CC_ALGO3' in globals():
            result_writer.writerow(['buffersize',CC_ALGO1,CC_ALGO1+'Start',CC_ALGO2,CC_ALGO2+'Start',\
                CC_ALGO3,CC_ALGO3+'Start', 'std'+CC_ALGO1,'std'+CC_ALGO2,'std'+CC_ALGO3, \
                CC_ALGO1+'_testruns',CC_ALGO2+'_testruns', CC_ALGO3+'_testruns'])

            for key in sorted(output.keys(), key=lambda x: float(x)):
                result_writer.writerow([key,
                                        np.mean(output[key][0]),
                                        np.mean(output[key][1]),
                                        np.mean(output[key][2]),
                                        np.mean(output[key][3]),
                                        np.mean(output[key][4]),
                                        np.mean(output[key][5]),
                                        np.std(output[key][1]),
                                        np.std(output[key][3]),
                                        np.std(output[key][5]),
                                        len(output[key][0]),
                                        len(output[key][2]),
                                        len(output[key][4]),
                                        ])
        else:
            result_writer.writerow(['buffersize',CC_ALGO1,CC_ALGO1+'Start',CC_ALGO2,CC_ALGO2+'Start',\
                'std'+CC_ALGO1,'std'+CC_ALGO2,CC_ALGO1+'_testruns',CC_ALGO2+'_testruns'])

            for key in sorted(output.keys(), key=lambda x: float(x)):
                result_writer.writerow([key,
                                        np.mean(output[key][0]),
                                        np.mean(output[key][1]),
                                        np.mean(output[key][2]),
                                        np.mean(output[key][3]),
                                        np.std(output[key][1]),
                                        np.std(output[key][3]),
                                        len(output[key][0]),
                                        len(output[key][2]),
                                        ])

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
