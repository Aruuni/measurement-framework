from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.clean import cleanup

import os
import sys
import subprocess
import time
import argparse


def get_git_revision_hash():
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'], stderr=subprocess.PIPE).rstrip()
    except subprocess.CalledProcessError as e:
        return 'unknown'


def get_host_version():
    try:
        return subprocess.check_output(['uname', '-ovr'], stderr=subprocess.PIPE).rstrip()
    except subprocess.CalledProcessError as e:
        return 'unknown'


class DumbbellTopo(Topo):
    "Three switchs connected to n senders and receivers."

    def build(self, n=2):
        switch1 = self.addSwitch('s1')
        switch2 = self.addSwitch('s2')
        switch3 = self.addSwitch('s3')

        self.addLink(switch1, switch2)
        self.addLink(switch2, switch3)

        for h in range(n):
            host = self.addHost('h%s' % h, cpu=.5 / n)
            self.addLink(host, switch1)
            receiver = self.addHost('r%s' % h, cpu=.5 / n)
            self.addLink(receiver, switch3)


def print_timer(complete, current):
    share = current * 100.0 / complete

    string = '  {: 5.2f}% ['.format(share)
    string += '=' * int(share / 10 * 3)
    string += ' ' * (30 - int(share / 10 * 3))
    string += '] {: 4}s remaining   '.format(complete - current)

    sys.stdout.write('%s\r' % string)
    sys.stdout.flush()


def get_available_algorithms():
    try:
        return subprocess.check_output(['sysctl net.ipv4.tcp_available_congestion_control '
                                        '| sed -ne "s/[^=]* = \(.*\)/\\1/p"'], shell=True)
    except subprocess.CalledProcessError as e:
        print('Cannot retrieve available congestion control algorithms.')
        print(e)
        return ''


def parseConfigFile(file):
    cc_algorithms = get_available_algorithms()

    unknown_alorithms = []

    output = []
    f = open(file)
    for line in f:
        line = line.replace('\n', '').strip()

        if len(line) > 1:
            if line[0] == '#':
                continue

        split = line.split(',')
        if split[0] == '':
            continue
        command = split[0].strip()

        if command == 'host':
            if len(split) != 5:
                print('Too few arguments to add host in line\n{}'.format(line))
                continue
            algorithm = split[1].strip()
            rtt = split[2].strip()
            start = float(split[3].strip())
            stop = float(split[4].strip())
            if algorithm not in cc_algorithms:
                if algorithm not in unknown_alorithms:
                    unknown_alorithms.append(algorithm)
                continue
            output.append({
                'command': command,
                'algorithm': algorithm,
                'rtt': rtt,
                'start': start,
                'stop': stop})

        elif command == 'link':
            if len(split) != 4:
                print('Too few arguments to change link in line\n{}'.format(line))
                continue
            change = split[1].strip()
            if change != 'bw' and change != 'rtt':
                print('Unknown link option "{} in line\n{}'.format(change, line))
                continue
            value = split[2].strip()
            start = float(split[3].strip())
            output.append({
                'command': command,
                'change': change,
                'value': value,
                'start': start
            })
        else:
            print('Skip unknown command "{}" in line\n{}'.format(command, line))
            continue

    if len(unknown_alorithms) > 0:
        print('Uninstalled or unknown congestion control algorithm:\n  ' + ' '.join(unknown_alorithms))
        print('Available algorithms:\n  ' + cc_algorithms.strip())

    return output


def check_tools():
    missing_tools = []
    tools = {
        'tcpdump': 'tcpdump',
        'ethtool': 'ethtool',
        'netcat': 'netcat',
        'moreutils': 'ts'
    }

    for package, tool in tools.items():
        try:
            process = subprocess.Popen(['which', tool], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = process.communicate()[0]
            if out == "":
                missing_tools.append(package)
        except (OSError, subprocess.CalledProcessError) as e:
            missing_tools.append(package)

    if len(missing_tools) > 0:
        print('Missing tools. Please run')
        print('  apt install ' + ' '.join(missing_tools))

    return len(missing_tools)


def sleep_progress_bar(seconds, current_time, complete):
    print_timer(complete=complete, current=current_time)
    while seconds > 0:
        time.sleep(min(1, seconds))
        current_time = current_time + min(1, seconds)
        print_timer(complete=complete, current=current_time)
        seconds -= 1
    return current_time


def run_test(commands, directory, name, bandwidth, initial_rtt, buffer_size, buffer_latency, poll_interval):
    duration = 0
    start_time = 0
    number_of_hosts = 0

    output_directory = os.path.join(directory, '{}_{}'.format(time.strftime('%m%d_%H%M%S'), name))

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    write_config = [
        'Test Name: {}'.format(name),
        'Date: {}'.format(time.strftime('%c')),
        'Kernel: {}'.format(get_host_version()),
        'Git Commit: {}'.format(get_git_revision_hash()),
        'Initial Bandwidth: {}'.format(bandwidth),
        'Burst Buffer: {}'.format(buffer_size),
        'Buffer Latency: {}'.format(buffer_latency),
        'Commands: '
    ]
    for cmd in commands:
        start_time += cmd['start']

        config_line = '{}, '.format(cmd['command'])
        if cmd['command'] == 'link':
            config_line += '{}, {}, {}'.format(cmd['change'], cmd['value'], cmd['start'])
        elif cmd['command'] == 'host':
            number_of_hosts += 1
            config_line += '{}, {}, {}, {}'.format(cmd['algorithm'], cmd['rtt'], cmd['start'], cmd['stop'])
            if start_time + cmd['stop'] > duration:
                duration = start_time + cmd['stop']
        write_config.append(config_line)

    with open(os.path.join('{}'.format(output_directory), 'parameters.txt'), 'w') as f:
        f.write('\n'.join(write_config))
        f.close()

    print('-' * 60)
    print('Starting test: {}'.format(name))
    print('{}'.format(time.strftime('%c')))
    print('Total duration: {}s'.format(duration))

    time.sleep(1)
    topo = DumbbellTopo(number_of_hosts)
    net = Mininet(topo=topo, link=TCLink)
    net.start()

    # start tcp dump
    try:
        subprocess.Popen(['tcpdump', '-i', 's1-eth1', '-n', 'tcp', '-s', '88',
                          '-w', os.path.join(output_directory, 's1.pcap')])
        subprocess.Popen(['tcpdump', '-i', 's3-eth1', '-n', 'tcp', '-s', '88',
                          '-w', os.path.join(output_directory, 's3.pcap')])
    except Exception as e:
        print('Error on starting tcpdump\n{}'.format(e))
        exit(1)

    time.sleep(1)

    host_counter = 0
    for cmd in commands:
        if cmd['command'] != 'host':
            continue
        send = net.get('h{}'.format(host_counter))
        send.setIP('10.1.0.{}/8'.format(host_counter))
        recv = net.get('r{}'.format(host_counter))
        recv.setIP('10.2.0.{}/8'.format(host_counter))
        host_counter += 1

        # setup FQ, algorithm, netem, nc host
        send.cmd('tc qdisc add dev {}-eth0 root fq pacing'.format(send))
        send.cmd('ip route change 10.0.0.0/8 dev {}-eth0 congctl {}'.format(send, cmd['algorithm']))
        send.cmd('ethtool -K {}-eth0 tso off'.format(send))
        recv.cmd('tc qdisc add dev {}-eth0 root netem delay {}'.format(recv, cmd['rtt']))
        recv.cmd('timeout {} nc -klp 9000 > /dev/null &'.format(duration))

        # pull BBR values
        send.cmd('./ss_script.sh {} >> {}.bbr &'.format(poll_interval, os.path.join(output_directory, send.IP())))

    s2, s3 = net.get('s2', 's3')
    s2.cmd('tc qdisc add dev s2-eth2 root tbf rate {} buffer {} latency {}'.format(
        bandwidth, buffer_size, buffer_latency))

    netem_running = False
    if initial_rtt != '0ms':
        netem_running = True
        s2.cmd('tc qdisc add dev s2-eth1 root netem delay {}'.format(initial_rtt))
    s2.cmd('./buffer_script.sh {0} {1} >> {2}.buffer &'.format(poll_interval, 's2-eth2',
                                                               os.path.join(output_directory, 's2-eth2-tbf')))

    complete = duration
    current_time = 0

    host_counter = 0

    try:
        for cmd in commands:
            start = cmd['start']
            current_time = sleep_progress_bar(start, current_time=current_time, complete=complete)

            if cmd['command'] == 'link':
                s2 = net.get('s2')
                if cmd['change'] == 'bw':
                    s2.cmd('tc qdisc change dev s2-eth2 root tbf rate {} buffer {} latency {}'.format(
                        cmd['value'], buffer_size, buffer_latency))
                    log_String = 'Change bandwidth to {}.'.format(cmd['value'])
                elif cmd['change'] == 'rtt':
                    if netem_running:
                        s2.cmd('tc qdisc change dev s2-eth1 root netem delay {}'.format(cmd['value']))
                    else:
                        s2.cmd('tc qdisc add dev s2-eth1 root netem delay {}'.format(cmd['value']))
                    log_String = 'Change rtt to {}.'.format(cmd['value'])

            elif cmd['command'] == 'host':
                send = net.get('h{}'.format(host_counter))
                recv = net.get('r{}'.format(host_counter))
                timeout = cmd['stop']
                log_String = 'h{}: {} {}, {} -> {}'.format(host_counter, cmd['algorithm'], cmd['rtt'], send.IP(), recv.IP())
                send.cmd('timeout {} nc {} 9000 < /dev/urandom > /dev/null &'.format(timeout, recv.IP()))
                host_counter += 1
            print(log_String + ' ' * (60 - len(log_String)))

        current_time = sleep_progress_bar((complete - current_time) % 1, current_time=current_time, complete=complete)
        current_time = sleep_progress_bar(complete - current_time, current_time=current_time, complete=complete)
    except (KeyboardInterrupt, Exception) as e:
        print(e)
    finally:
        print('\nExiting...')
        net.stop()
        cleanup()


if __name__ == '__main__':

    if check_tools() > 0:
        exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('config', metavar='CONFIG',
                        help='Path to the config file.')
    parser.add_argument('-b', dest='bandwidth',
                        default='10Mbit', help='Initial bandwidth of the bottleneck link. (default: 10mbit)')
    parser.add_argument('-r', dest='rtt',
                        default='0ms', help='Initial rtt for all flows. (default 0ms)')
    parser.add_argument('-d', dest='directory',
                        default='test/', help='Path to the output directory. (default: test/)')
    parser.add_argument('-s', dest='buffer_size',
                        default='1600b', help='Burst size of the token bucket filter. (default: 1600b)')
    parser.add_argument('-l', dest='latency',
                        default='100ms', help='Maximum latency at the bottleneck buffer. (default: 100ms)')
    parser.add_argument('-n', dest='name',
                        default='TCP', help='Name of the output directory. (default: TCP)')
    parser.add_argument('--poll-interval', dest='poll_interval', type=float,
                        default=0.04, help='Interval to poll TCP values and buffer backlog in seconds. (default: 0.04)')

    args = parser.parse_args()
    if not os.path.isfile(args.config):
        print('Config file missing:\n{}'.format(args.config))
        sys.exit(-1)

    commands = parseConfigFile(args.config)
    if len(commands) == 0:
        print('No valid commands found in config file.\nExiting...')
        sys.exit(-1)

    # setLogLevel('info')
    run_test(bandwidth=args.bandwidth,
             initial_rtt=args.rtt,
             commands=commands,
             buffer_size=args.buffer_size,
             buffer_latency=args.latency,
             name=args.name,
             directory=args.directory,
             poll_interval=args.poll_interval)
