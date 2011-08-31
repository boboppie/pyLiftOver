#!/usr/bin/python

import sys
import tempfile
import subprocess
# Use core json for 2.6+, simplejson for <=2.5
try:
    import json
except ImportError:
    import simplejson as json


# if only one argument read from stdin
if len (sys.argv) == 3:
    print 'reading coords from: %s' % sys.argv[1]
    start_file = open(sys.argv[1])
elif len(sys.argv) == 2:
    start_file = tempfile.NamedTemporaryFile()
    for line in sys.stdin.readlines():
        print line
        start_file.write(line)
    #start_file.close()


    for line in start_file.readlines():
        print line
else:
    print 'Usage:\n\t%s start_file start_genome_build' % sys.argv[0]
    exit(1)

print 'start_file:', start_file.name, type(start_file)

new_coords_file = tempfile.NamedTemporaryFile()
unmapped_file = tempfile.NamedTemporaryFile()

subprocess.call(['./liftOver', start_file.name, 'hg17ToHg19.over.chain', new_coords_file.name, unmapped_file.name])

new_coords = []
for line in new_coords_file:
    new_coords.append(line)

unmapped = []
for line in unmapped_file:
    unmapped.append(line)

print 'new_coords:', new_coords
print 'unmapped:', unmapped

res = {'new_coords': new_coords, 'unmapped': unmapped}
print 'res:', res

print 'json:', json.dumps(res)

