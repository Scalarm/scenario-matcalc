#!/usr/bin/env python

# Creates <MATCALC_SCRIPT_NAME> file for mcc (see const value)
# Uses parameters witout "_" suffix found in rb_psc_st1.msc.template
# to replace parameters written with this suffix and create a script file for mcc.
# However, not all user-providede parameters are used for replacement - see:
# PARAMETER_REPLACE_EXCEPTIONS const.

__author__ = "Jakub Liput <Github: kliput>"

import scalarm
import os

MATCALC_SCRIPT_NAME = 'matcalc_input.mcs'
OUTPUT_FILE_NAME = 'matcalc_output'

PARAMETER_REPLACE_EXCEPTIONS = set([
    'HOMO_enabled',
    'HOTR_enabled',
    'OutputName'
])

# config represents a read input.json file
input_config = scalarm.InputReader()

# for example, to get "x" param use: config.x or config["x"]
# NOTE: values are strings - please convert them

output_config = ''

# not very efficient because copying string...
# use: http://stackoverflow.com/questions/6116978/python-replace-multiple-strings
with open('rb_psc_st1.mcs.template') as f:
    output_config = f.read().decode('utf8')
    for key, value in input_config:
        if key not in PARAMETER_REPLACE_EXCEPTIONS:
            print 'replace {key} -> {value}'.format(key=key, value=value)
            output_config = output_config.replace(key + '_', unicode(value))

output_config = output_config.replace('__WORKING_DIR__', os.getcwd())

# currently always enabled
output_config = output_config.replace('CAST_', "")

if input_config['HOMO_enabled'] == 'true':
    output_config = output_config.replace('HOMO_', "")
    print 'enabling HOMO'
    if input_config['HOTR_enabled'] == 'true':
        output_config = output_config.replace('HOTR_', "")
        print 'enabling HOTR'
    else:
        output_config = output_config.replace('HOTR_', "$")
        print 'disabling HOTR'
else:
    output_config = output_config.replace('HOMO_', "$")
    print 'enabling HOMO'
    # when HOMO is disabled, HOTR is always disabled
    output_config = output_config.replace('HOTR_', "$")
    print 'enabling HOTR'

# output files names are hardcoded, because we don't need to parametrize them
# NOTE that OUTPUT_FILE_NAME name is used in output reader
output_config = output_config.replace('OutputName_', OUTPUT_FILE_NAME)

with open(MATCALC_SCRIPT_NAME, 'w') as of:
    of.write(output_config.encode('utf8'))
