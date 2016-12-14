#!/usr/bin/env python

__author__ = "Jakub Liput <Github: kliput>"

import re
import subprocess
import sys
import threading
import os
import scalarm
import time
from socket import getfqdn, gethostname
from Queue import Empty, Queue

ON_POSIX = 'posix' in sys.builtin_module_names
MATCALC_SCRIPT_NAME = 'matcalc_input.mcs'
BINARY_NAME = 'mcc'
OUTPUT_POLLING_TIME_SEC = 1
DEFAULT_TIMEOUT_MINUTES = 90
RE_MCS_ERROR = re.compile(r'^\*\*\* error \*\*\*')

# Dictorinary host -> matcher object with .match method (regexp)
HOST_MATCHERS = {
    'zeus': re.compile('.*\.zeus'),
    'prometheus': re.compile('.*\.prometheus'),
    'jack': re.compile('jack')
}

# predefined matcalc root dirs for various machines
BINARY_DIRS = {
    'zeus': '/mnt/gpfs/work/plgrid/groups/plggvirtroll/matcalc',
    'prometheus': '/net/archive/groups/plggvirtroll/matcalc',
    'jack': '/home/matcalc/matcalc-5.62/matcalc'
}

def scalarm_log(message):
    print '[scalarm-simulation]', message

# Buffers output of process (out) into queue line by line.
# It allows to create separate thread which will buffer subprocess output
# and another thread to read output lines from queue.
# Thanks to: http://stackoverflow.com/a/4896288
def enqueue_output(out, queue):
    for out_line in iter(out.readline, b''):
        queue.put(out_line)
    out.close()

# Return a predefined host identifier (see HOST_MATCHERS keys) or None
# if host is not predefined for this script
def detect_host():
    fqdn = getfqdn()
    scalarm_log('FQDN: %s' % fqdn)

    hostname = gethostname()
    scalarm_log('Hostname: %s' % fqdn)

    host = None
    try:
        matched_hosts = [matcher[0] for matcher in HOST_MATCHERS.items() if matcher[1].match(hostname)]
        if len(matched_hosts) > 0:
            host = matched_hosts[0]
        else:
            host = [matcher[0] for matcher in HOST_MATCHERS.items() if matcher[1].match(fqdn)][0]
        scalarm_log('Detected host: %s' % host)
    except (KeyError, IndexError):
        scalarm_log('Host is not predefined in this script')

    return host

def kill_if_timeout(start_time, timeout_seconds, matcalc_process):
    time_elapsed = time.time() - start_time
    if time_elapsed > timeout_seconds:
        scalarm_log('Time limit exceeded (%d minutes %d seconds)' % (timeout_seconds/60, timeout_seconds % 60))
        scalarm_log('Terminating mcc process due to time limit.')
        matcalc_process.kill()
        sys.exit(matcalc_process.returncode)

def main():
    input_config = scalarm.InputReader()

    timeout_minutes = input_config['timeout_minutes']
    if timeout_minutes is not None:
        timeout_seconds = timeout_minutes*60
    else:
        timeout_seconds = DEFAULT_TIMEOUT_MINUTES*60

    scalarm_log('Timeout set to %d minutes %d seconds' % (timeout_seconds/60, timeout_seconds % 60))

    start_time = time.time()

    host = detect_host()

    # select matcalc root dir basing on hostname
    if host is None:
        matcalc_root = None
    else:
        matcalc_root = BINARY_DIRS[host]

    if matcalc_root is None:
        scalarm_log('"mcc" binary is assumed to be in PATH')
    binary_path = (matcalc_root is None) and BINARY_NAME or os.path.join(matcalc_root, BINARY_NAME)
    # command = binary_path + ' ./' + MATCALC_SCRIPT_NAME
    command = 'mcc'

    scalarm_log('Starting command: %s' % command)
    matcalc_process = subprocess.Popen(command.split(),
                                       shell=False,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       close_fds=ON_POSIX)

    output_queue = Queue()

    output_collector_thread = threading.Thread(
        target=enqueue_output,
        args=(matcalc_process.stdout, output_queue)
    )

    output_collector_thread.daemon = True
    output_collector_thread.start()

    process_ended = False

    while True:
        try:
            line = output_queue.get(True, OUTPUT_POLLING_TIME_SEC)
        except Empty:
            if process_ended:
                break
            elif matcalc_process.poll() is not None:
                scalarm_log(
                    'Detected Matcalc process end with exitcode: %s'
                    % matcalc_process.poll()
                )
                process_ended = True
            else:
                kill_if_timeout(start_time, timeout_seconds, matcalc_process)
        else:
            sys.stdout.write('[mcc] %s' % line)
            error_match = RE_MCS_ERROR.match(line)
            if error_match is not None:
                scalarm_log('MatCalc error detected! Terminating mcc process.')
                matcalc_process.kill()
                sys.exit(matcalc_process.returncode)
            else:
                kill_if_timeout(start_time, timeout_seconds, matcalc_process)

    scalarm_log('Exiting with exitcode: %d' % matcalc_process.poll())
    sys.exit(matcalc_process.poll())


if __name__ == '__main__':
    main()
