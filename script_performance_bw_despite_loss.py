from helper.csv_writer import read_csv
import glob
import sys
import os
import stat
import numpy as np
import argparse
import csv


RTT = 100
TEST = 'performance_bw_despite_loss'
RUN_SH = 'run_' + TEST + '.sh'
CC_ALGO = 'bbr'
DURATION = 180 


def generate_configs(dir):
    # Create directory for config files
    if not os.path.exists(dir):
        os.makedirs(dir)

    # Prepare steps 
    # steps = np.logspace(0, 2, 20, endpoint=False)
    #Round after 3 decimal places
    #steps = list(map(lambda x: round(x, -3), steps))
    # steps = list(map(lambda x: int(x),steps))
    steps =[1,2,3,4,5,6,7,10,13,16,20,25,32,40,50,63,80]
        
    # Write config into folder
    config = os.path.join(dir, '{}.conf'.format(TEST))
    with open(config, 'w') as config_file: 
        config_file.write('host, {}, {}ms, 0, {}\n'.format(CC_ALGO, RTT, DURATION))

    # Open file for commands
    with open(RUN_SH, 'w') as run_file:
        # Write commands to run_file 
        for step in steps:
            run_file.write('python run_mininet.py {0}/{1}.conf -n "{1}_{2}_{3:.3g}" --loss {3}%\n'.format(dir, TEST, CC_ALGO, step))
        run_file.write('python analyze.py -r -d test/\n')

    # Make run file executable
    st = os.stat(RUN_SH)
    os.chmod(RUN_SH, st.st_mode | stat.S_IEXEC)


def analyze(dir):
    output = {}

    for path, dirs, files in os.walk(dir):
        if 'csv_data' not in dirs:
            continue
        try:
            loss_rate = float(path.split('_')[-1])

        except Exception as e:
            sys.stderr.write('Skipping directory {}\n{}\n'.format(path, e))
            continue

        if not loss_rate in output.keys():
            output[loss_rate] = ([])

        if not os.path.exists(os.path.join(path, 'csv_data', 'throughput.csv.gz')):
            print('Skipping {}'.format(path))

        throughput = read_csv(os.path.join(path, 'csv_data', 'throughput.csv'))

        # Divide throughput of flows by aggregated throughput
        output[loss_rate].append(np.mean(throughput[0][1]))

    result_file_name = 'result_{}_{}.csv'.format(TEST, CC_ALGO)
    with open(result_file_name, 'wb') as result_file:
        result_writer = csv.writer(result_file, delimiter=';')
        print('lossrate, {0}, std_{0}, testruns').format(CC_ALGO)
        result_writer.writerow(['lossrate', CC_ALGO, 'std_'+ CC_ALGO, 'testruns'])

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
