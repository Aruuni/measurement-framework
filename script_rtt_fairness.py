import numpy as np
import os
import stat
import sys
import argparse
from helper.csv_writer import read_csv
import csv


BUFFERSIZE = 0.24
TEST = 'rtt_fairness'
RUN_SH = 'run_' + TEST + '.sh'
CC_ALGO = 'bbr'
DURATION = 50
TESTRUNS = 5


def generate_configs(dir):
    # Create directory for config files
    if not os.path.exists(dir):
        os.makedirs(dir)

    # Prepare steps
    steps = np.arange(10, 110, 10).tolist() 

    # Open file for commands
    with open(RUN_SH, 'w') as run_file:
        for rtt_flow_one in steps:
            for rtt_flow_two in steps:
            # Write config into folder
                config = os.path.join(dir, TEST+'_{}_{}_{}.conf'.format(CC_ALGO, rtt_flow_one, rtt_flow_two))
                with open(config, 'w') as config_file: 
                    config_file.write('host, {}, {}ms, 0, {}\n'.format(CC_ALGO, rtt_flow_one, DURATION - 3))
                    config_file.write('host, {}, {}ms, 3, {}\n'.format(CC_ALGO, rtt_flow_two, DURATION))
            
                run_file.write('python run_mininet.py {}/rtt_fairness_{}_{}_{}.conf\n'.format(dir, CC_ALGO, rtt_flow_one, rtt_flow_two))

    # Make run file executable
    st = os.stat(RUN_SH)
    os.chmod(RUN_SH, st.st_mode | stat.S_IEXEC)


def analyze(dir):
    output = {}
    for path, dirs, files in os.walk(dir):
        if 'csv_data' not in dirs:
            continue
        try:
            rtt_flow_two = float(path.split('_')[-1])
            rtt_flow_one = float(path.split('_')[-2])

        except Exception as e:
            sys.stderr.write('Skipping directory {}\n{}\n'.format(path, e))
            continue
        
        rtts = rtt_flow_one*1000 + rtt_flow_two
        if rtts not in output.keys():
            output[rtts] = ([], [], [])

        if not os.path.exists(os.path.join(path, 'csv_data', 'throughput.csv.gz')):
            print('Skipping {}'.format(path))

        throughput = read_csv(os.path.join(path, 'csv_data', 'throughput.csv'))

        flow_1 = 0
        flow_2 = 1

        send_flow_1 = np.average(throughput[flow_1][1])
        send_flow_2 = np.average(throughput[flow_2][1])
        send_total = send_flow_1 + send_flow_2
        avg_fairness = (send_flow_1 + send_flow_2) ** 2 / (send_flow_1 ** 2 + send_flow_2 ** 2) / 2

        flow_1_share = 0
        flow_2_share = 0

        if send_total > 0:
            flow_1_share = send_flow_1 / send_total
            flow_2_share = send_flow_2 / send_total

        output[rtts][0].append(flow_1_share)
        output[rtts][1].append(flow_2_share)
        output[rtts][2].append(avg_fairness)

    result_file_name = 'result_{}_{}_{}.csv'.format(TEST, CC_ALGO, CC_ALGO)
    with open(result_file_name, 'wb') as result_file:
        result_writer = csv.writer(result_file, delimiter=';')
        result_writer.writerow(['rtt', CC_ALGO+'flow_1_share', CC_ALGO+'flow_2_share', 'avg_fairness', 'stdev', 'testruns'])

        for key in sorted(output.keys(), key=lambda x: float(x)):
            values = [
                key,
                np.average(output[key][0]),
                np.average(output[key][1]),
                np.average(output[key][2]),
                np.std(output[key][0]),
                len(output[key][0])
            ]
            result_writer.writerow(values)


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