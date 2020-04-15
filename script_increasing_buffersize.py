from helper.csv_writer import read_csv
import glob
import sys
import os
import stat
import numpy as np
import argparse


RTT = 50
RUN_SH = 'run_buffersize.sh'
CC_ALGO1 = 'cubic'
CC_ALGO2 = 'bbr'
DURATION = 180 


def generate_configs(dir):
    # Create directory for config files
    if not os.path.exists(dir):
        os.makedirs(dir)

    # Prepare steps
    steps = np.arange(0.1, 3, 0.1).tolist() + np.arange(3, 10, 0.5).tolist() + np.arange(10, 55, 5).tolist()
    steps = list(map(lambda x: round(x, 1), steps))
        
    # Write config into folder
    config = os.path.join(dir, 'buffersize.conf')
    with open(config, 'w') as config_file: 
        config_file.write('host, {}, {}ms, 0, {}\n'.format(CC_ALGO1, RTT, DURATION))
        config_file.write('host, {}, {}ms, 1, {}\n'.format(CC_ALGO2, RTT, DURATION - 1))

    # Open file for commands
    with open(RUN_SH, 'w') as run_file:
        # Write commands to run_file 
        for step in steps:
            run_file.write('python run_mininet.py {}/buffersize.conf -n "buffersize_{}" -l {}ms\n'.format(dir, step, step * RTT))

    # Make run file executable
    st = os.stat(RUN_SH)
    os.chmod(RUN_SH, st.st_mode | stat.S_IEXEC)


def analyze(dir):
    output = {}

    for path, dirs, files in os.walk(dir):
        if 'csv_data' not in dirs:
            continue
        try:
            buffer_size = float(path.split('_')[-1])

        except Exception as e:
            sys.stderr.write('Skipping directory {}\n{}\n'.format(path, e))
            continue

        if not buffer_size in output.keys():
            output[buffer_size] = ([], [])

        if not os.path.exists(os.path.join(path, 'csv_data', 'throughput.csv.gz')):
            print('Skipping {}'.format(path))

        throughput = read_csv(os.path.join(path, 'csv_data', 'throughput.csv'))
        fairness = read_csv(os.path.join(path, 'csv_data', 'fairness.csv'))['Throughput'][1]

        avg_fairness = np.median(fairness[int(len(fairness)*0.8):])

        if avg_fairness > 0.999 or np.abs(avg_fairness - 0.5) < 0.01:
            # something might have went wrong with this data
            print(buffer_size, path)

        # Divide throughput of switch 1 by switch 3
        output[buffer_size][0].append(np.mean(throughput[0][1]) / np.mean(throughput[2][1]))
        output[buffer_size][1].append(np.mean(throughput[1][1]) / np.mean(throughput[2][1]))

    print('buffersize;{0};{1};fairness;std_{0};std_{1}').format(CC_ALGO1, CC_ALGO2)

    for buffersize in sorted(output.keys()):
        cc_algo1_values = output[buffersize][0]
        cc_algo2_values = output[buffersize][1]

        fairness = (np.mean(cc_algo1_values) + np.mean(cc_algo2_values)) ** 2 / 2 / \
                   (np.mean(cc_algo1_values) ** 2 + np.mean(cc_algo2_values) ** 2)

        values = [
            buffersize,
            np.mean(cc_algo1_values),
            np.mean(cc_algo2_values),
            fairness,
            np.std(cc_algo1_values),
            np.std(cc_algo2_values)
        ]

        print(';'.join(map(str, values)))


if __name__ == '__main__':
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
