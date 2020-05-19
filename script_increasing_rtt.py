import numpy as np
import os
import stat
import sys
import argparse
from helper.csv_writer import read_csv
import csv


BUFFERSIZE = 0.24
TEST = 'increasing_rtt'
RUN_SH = 'run_' + TEST + '.sh'
CC_ALGO1 = 'bbr'
CC_ALGO2 = 'bbr2'
DURATION = 180
TESTRUNS = 5


def generate_configs(dir):
    # Create directory for config files
    if not os.path.exists(dir):
        os.makedirs(dir)

    # Prepare steps
    steps = np.arange(10, 50, 5).tolist() + np.arange(50, 160, 10).tolist() \
            + np.arange(160, 300, 20).tolist() + np.arange(300, 600, 50).tolist() \
            + np.arange(600, 1100, 100).tolist()

    # Open file for commands
    with open(RUN_SH, 'w') as run_file:
        for rtt in steps:
            # Write config into folder
            config = os.path.join(dir, TEST+'{}ms.conf'.format(rtt))
            with open(config, 'w') as config_file: 
                config_file.write('host, {}, {}ms, 0, {}\n'.format(CC_ALGO1, rtt, DURATION))
                config_file.write('host, {}, {}ms, 1, {}\n'.format(CC_ALGO2, rtt, DURATION - 1))

            # Write commands to run_file
            buffer = rtt * BUFFERSIZE
            for i in range(TESTRUNS):
                run_file.write('python run_mininet.py -l {}ms {} -n "increasing_rtt_{}_{}_{}"\n'.format(buffer, config, CC_ALGO1, CC_ALGO2, rtt))

    # Make run file executable
    st = os.stat(RUN_SH)
    os.chmod(RUN_SH, st.st_mode | stat.S_IEXEC)


def analyze(dir):
    output = {}
    for path, dirs, files in os.walk(dir):
        if 'csv_data' not in dirs:
            continue
        try:
            rtt = float(path.split('_')[-1])

        except Exception as e:
            sys.stderr.write('Skipping directory {}\n{}\n'.format(path, e))
            continue

        if rtt not in output.keys():
            output[rtt] = ([], [], [])

        if not os.path.exists(os.path.join(path, 'csv_data', 'throughput.csv.gz')):
            print('Skipping {}'.format(path))

        throughput = read_csv(os.path.join(path, 'csv_data', 'throughput.csv'))

        cc_algo1 = 0
        cc_algo2 = 1

        send_cc_algo1 = np.average(throughput[cc_algo1][1][400:])
        send_cc_algo2 = np.average(throughput[cc_algo2][1][400:])
        send_total = send_cc_algo1 + send_cc_algo2
        avg_fairness = (send_cc_algo1 + send_cc_algo2) ** 2 / (send_cc_algo1 ** 2 + send_cc_algo2 ** 2) / 2

        cc_algo1_share = 0
        cc_algo2_share = 0

        if send_total > 0:
            cc_algo1_share = send_cc_algo1 / send_total
            cc_algo2_share = send_cc_algo2 / send_total

        output[rtt][0].append(cc_algo1_share)
        output[rtt][1].append(cc_algo2_share)
        output[rtt][2].append(avg_fairness)

    result_file_name = 'result_{}_{}_{}.csv'.format(TEST, CC_ALGO1, CC_ALGO2)
    with open(result_file_name, 'wb') as result_file:
        result_writer = csv.writer(result_file, delimiter=';')
        result_writer.writerow(['rtt', CC_ALGO1+'_share', CC_ALGO2+'_share', 'avg_fairness', 'stdev', 'testruns'])

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