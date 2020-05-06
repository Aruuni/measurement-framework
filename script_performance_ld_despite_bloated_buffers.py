from helper.csv_writer import read_csv
import glob
import sys
import os
import stat
import numpy as np
import argparse
import csv


RTT = 40
# BANDWIDTH = '128kbps' from cardwells plot, now using default 10Mbit
BANDWIDTH = 10
TEST = 'performance_ld_despite_bloated_buffers'
RUN_SH = 'run_' + TEST + '.sh'
CC_ALGO = 'bbr'
DURATION = 180 


def generate_configs(dir):
    # Create directory for config files
    if not os.path.exists(dir):
        os.makedirs(dir)

    # Prepare steps 
    steps = np.logspace(1, 5, 20, endpoint=True)
    #Round after 3 decimal places
    steps = list(map(lambda x: round(x, 1), steps))
        
    # Write config into folder
    config = os.path.join(dir, '{}.conf'.format(TEST))
    with open(config, 'w') as config_file: 
        #for i in range(8):
        config_file.write('host, {}, {}ms, 0, {}\n'.format(CC_ALGO, RTT, DURATION))

    # Open file for commands
    with open(RUN_SH, 'w') as run_file:
        # Write commands to run_file 
        for step in steps:
            # latency = buffersize/BW
            latency = step/(BANDWIDTH*1000/8)*1000
            run_file.write('python run_mininet.py {0}/{1}.conf -n "{1}_{2}_buffersize_{3}" -l {4}ms\n'.format(dir, TEST, CC_ALGO, step, latency))

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
            output[buffer_size] = ([])

        if not os.path.exists(os.path.join(path, 'csv_data', 'rtt.csv.gz')):
            print('Skipping {}'.format(path))

        latency = read_csv(os.path.join(path, 'csv_data', 'rtt.csv'))

        output[buffer_size].append(np.mean(latency[0][1]))
        result_file_name = 'result_{}_{}.csv'.format(TEST, CC_ALGO)

    with open(result_file_name, 'wb') as result_file:
        result_writer = csv.writer(result_file, delimiter=';')
        result_writer.writerow(['buffersize', CC_ALGO, 'std_'+ CC_ALGO, 'testruns'])

        for lossrate in sorted(output.keys()):
            cc_algo_values = output[lossrate]

            values = [
                lossrate,
                np.mean(cc_algo_values),
                np.std(cc_algo_values),
                len(output[lossrate])
            ]

            print(';'.join(map(str, values)))
            result_writer.writerow(values)


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
