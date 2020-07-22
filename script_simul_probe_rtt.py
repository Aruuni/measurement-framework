from helper.csv_writer import read_csv
import sys
import os
import stat
import numpy as np
import argparse
import ast

TEST = 'simul_probe_rtt'
RUN_SH = 'run_' + TEST + '.sh'
CC_ALGO = 'bbr'
DURATION = 120

def generate_configs(dir):
    # Create directory for config files
    if not os.path.exists(dir):
        os.makedirs(dir)

    # Prepare steps 
    steps = np.arange(1, 20, 1).tolist() + np.arange(20, 40, 2).tolist() \
            + np.arange(40, 100, 10).tolist() + np.arange(100, 220, 20).tolist()

    # Open file for commands
    with open(RUN_SH, 'w') as run_file:
        config = os.path.join(dir, '{}.conf'.format(TEST))
        for rtt in steps:
            # Write config into folder
            config = os.path.join(dir, TEST+'_{}_{}.conf'.format(CC_ALGO, rtt))
            with open(config, 'w') as config_file: 
                for i in range(1, 5):
                    config_file.write('host, {}, {}ms, 0, {}\n'.format(CC_ALGO, rtt, DURATION))

            # Write commands to run_file
            run_file.write('python run_mininet.py -l 500ms {}/{}_{}_{}.conf\n'.format(dir, TEST, CC_ALGO, rtt))
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
            rtt = path.split('_')[-1]
        except Exception as e:
            sys.stderr.write('Skipping directory {}\n{}\n'.format(path, e))
            continue

        info_file = os.path.join(path, 'csv_data', 'values.info')
        bbr_file = os.path.join(path, 'csv_data', 'bbr_values.csv.gz')

        if os.path.exists(info_file) and os.path.exists(bbr_file):

            f = open(info_file)
            f.readline()
            f.readline()
            f.readline()

            probe_rtt_durations = ast.literal_eval(f.readline().strip())[1:-1]
            f.close()

            bbr_values = read_csv(bbr_file, 6)
            single_probe_rtt_durations = []

            for c in bbr_values:
                start = -1
                ts = bbr_values[c][0]
                window = bbr_values[c][4]
                for i, t in enumerate(ts):
                    if float(window[i]) == 1:
                        if start < 0:
                            start = t
                    else:
                        if start > 0:
                            single_probe_rtt_durations.append((t - start) * 1000)
                            start = -1

            if rtt not in output:
                output[rtt] = (rtt, probe_rtt_durations, single_probe_rtt_durations)
            else:
                output[rtt] = (rtt, sorted(output[rtt][1] + probe_rtt_durations),
                               sorted(output[rtt][2] + single_probe_rtt_durations))

    values = []
    for i in output:
        values.append(output[i])

    values = sorted(values, key=lambda x: int(x[0]))

    print(';'.join([
        'rtt', 'sync_probertt_avg', 'sync_probertt_min', 'sync_probertt_max', 'sync_probertt_std',
        'single_probertt_avg', 'single_probertt_min', 'single_probertt_max', 'single_probertt_std'
    ]))
    for i in values:
        sync = i[1]
        single = i[2]
        if len(sync) is 0:
            continue
        print "{};{};{};{};{};{};{};{};{};".format(i[0],
                        np.average(sync), min(sync), max(sync), np.std(sync),
                        np.average(single), min(single), max(single), np.std(single))


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