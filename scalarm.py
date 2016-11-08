# Library with classes/functions for building Scalarm simulation scenarios
# License: MIT
# Copyright (c) Jakub Liput 2015-2016

import json
import os
import sys
import tarfile
from contextlib import closing

class InputReader(object):
    def __init__(self, path='input.json'):
        with open(path, 'rb') as f:
            self._input_contents = json.loads(f.read())

    def get_param(self, name):
        return self._input_contents[name]

    def __getattr__(self, name):
        return self.get_param(name)

    def __getitem__(self, name):
        return self.get_param(name)

    def __iter__(self):
        self._scal_i = 0
        return self

    def next(self):
        items = self.__dict__['_input_contents'].items()
        i = self.__dict__['_scal_i']
        n = len(items)
        if i < n:
            self._scal_i += 1
            return items[i]
        else:
            raise StopIteration()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        pass

class OutputWriter(object):
    def __init__(self):
        self.__dict__['_status'] = 'ok'
        self.__dict__['_reason'] = 'Reason not set'
        self.__dict__['_results_dict'] = {}
        self.__dict__['_output_files'] = []

    def set_error(self, reason):
        self.__dict__['_status'] = 'error'
        self.__dict__['_reason'] = reason

    def add_result(self, name, value):
        self._results_dict[name] = value

    def add_file(self, name):
        self.__dict__['_output_files'].append(name)

    def __setattr__(self, name, value):
        return self.add_result(name, value)

    def __setitem__(self, name, value):
        return self.add_result(name, value)

    def _write_moes(self):
        with open('output.json', 'w+') as f:
            if self._status == 'ok':
                json.dump({'status': self._status,
                           'results': self._results_dict},
                          f)
            elif self._status == 'error':
                json.dump({'status': self._status,
                           'reason': self._reason},
                          f)
            else:
                json.dump({'status': 'error',
                           'reason': 'Wrong status set: %s' % self._status},
                f)

    def _write_binary(self):
        with closing(tarfile.open('output.tar.gz', "w:gz")) as tar:
            for name in self._output_files:
                tar.add(name)

    def write(self):
        self._write_moes()
        if len(self._output_files) > 0:
            self._write_binary()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.write()

def import_binaries():
    files_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    for name in os.listdir(files_dir):
        try:
            os.symlink(os.path.join(files_dir, name), name)
        except OSError, e:
            if e.errno == os.errno.EEXIST:
                print '[scalarm-simulation] simulation file already exists in working dir: %s' % (name)
                pass
                #os.remove(name)
                #os.symlink(os.path.join(files_dir, name), name)

# LAUNCH IMPORT BINARIES
import_binaries()
