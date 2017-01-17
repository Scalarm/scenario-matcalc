#!/usr/bin/env python2

__author__ = "Jakub Liput <Github: kliput>"

import scalarm
import glob
import os

OUTPUT_FILE_NAME = 'matcalc_output'

def main():
    exitcode = 0
    error = None
    if os.path.exists('_exitcode'):
        with open('_exitcode') as exitcode_f:
            content = exitcode_f.read().split(',')
            exitcode = int(content[0])
            error = ''.join(content[1:])

    # output represents output.json file
    # you can add output values with output.x = value or output["x"] = value
    with scalarm.OutputWriter() as output:
        if exitcode != 0:
            output.set_error('mcc exited with exitcode {ec}; error reason: {er}'.format(
                ec=exitcode,
                er=error
            ))
        else:
            # currently we have no MoE output
            output.example = 1

            # NOTE: paths are relative to script's working dir
            os.mkdir('dist')
            for name in glob.glob('*.dist'):
                os.rename(name, os.path.join('dist', name))
            output.add_file('dist')

            output.add_file(OUTPUT_FILE_NAME)

if __name__ == '__main__':
    main()
