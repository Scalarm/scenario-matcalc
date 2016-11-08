#!/usr/bin/env python2

__author__ = "Jakub Liput <Github: kliput>"

import scalarm
import glob
import os

OUTPUT_FILE_NAME = 'matcalc_output'

# output represents output.json file
# you can add output values with output.x = value or output["x"] = value
with scalarm.OutputWriter() as output:
    # currently we have no MoE output
    output.example = 1

    # NOTE: paths are relative to script's working dir
    os.mkdir('dist')
    for name in glob.glob('*.dist'):
        os.rename(name, os.path.join('dist', name))
    output.add_file('dist')

    output.add_file(OUTPUT_FILE_NAME)
