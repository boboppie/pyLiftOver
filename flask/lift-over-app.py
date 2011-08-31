from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
from collections import defaultdict
from functools import wraps
# Use core json for 2.6+, simplejson for <=2.5
try:
    import json
except ImportError:
    import simplejson as json


app = Flask(__name__)
app.config.from_object(__name__)

DEBUG = True
CHAIN_DIR = '.'

abbrevs = {'human': 'hg',
           'mouse': 'mm'}

organism_order = ['human', 'mouse']

def support_jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f(*args,**kwargs).data) + ')'
            return app.response_class(content, mimetype='application/json')
        else:
            return f(*args, **kwargs)
    return decorated_function


@app.route('/lift/<organism>', methods=['POST', 'GET'])
@support_jsonp
def lift(organism):

    chains = get_chain_files(organism)

    if request.method == 'GET':
        # not support file upload and asynchronous
        start_coords = request.args.get('coords','')
        source = request.args.get('source','')
        target = request.args.get('target','')

        print 'source = %s, target = %s' % (source, target)

        print 'coords: ', start_coords
        #return str(json.dumps(chains))
    else:
        print 'REQUEST FORM: ', request.form
        source = request.form['source']
        target = request.form['target']

        print 'source = %s, target = %s' % (source, target)

        if 'coords' in request.files:
            start_coords = request.files['coords']
        else:
            start_coords = request.form['coords']
        print 'coords: ', start_coords

    chain_file = get_chain_file(source, target, chains)
    if not chain_file:
        return "Can't convert from " + source + " to " + target

    res = do_liftover(start_coords, chain_file)
    res['version'] = target
    res['organism'] = organism
    res['format'] = 'BED'
    print 'GOT RESULTS:', res
    return jsonify(res)


@app.route('/lift/versions/<organism>', methods=['GET'])
@support_jsonp
def sources(organism):
    chains = get_chain_files(organism)
    versions = defaultdict(list)
    for source, targets in chains.items():
        if not source in versions['sources']:
            versions['sources'].append(source)
        for target in targets:
            if not target in versions['targets']:
                versions['targets'].append(target)
    versions['sources'].sort()
    versions['targets'].sort()
    return jsonify(versions)
    #return json.dumps(versions)

@app.route('/lift/organisms', methods=['GET'])
@support_jsonp
def organisms():
    organisms = []
    chains = read_chain_files()
    for organism in organism_order:
    #for (organism, abbrev) in abbrevs.items():
        abbrev = abbrevs[organism]
        print 'organism: ', organism, abbrev
        for chain in chains:
            if chain.startswith(abbrev):
                organisms.append(organism)
                break
    return jsonify({'organisms': organisms})

def get_chain_file(source, target, chains):
    try:
        return chains[source][target]
    except KeyError:
        return None

chain_files = []
def read_chain_files():
    if len(chain_files) == 0:
        for f in os.listdir(CHAIN_DIR):
            chain_files.append(f)
    return chain_files

def get_chain_files(organism):
    chains = defaultdict(dict)
    abbrev = abbrevs[organism]
    # TODO check for null abbrev

    for f in read_chain_files():
        if f.startswith(abbrev) and f.endswith('over.chain'):
            mapping = f[:f.find('.')]
            parts = mapping.split('To')
            from_version = parts[0].lower()
            to_version = parts[1].lower()
            chains[from_version][to_version] = f
    return chains

def do_liftover(start_coords, chain_file):
    start_file = tempfile.NamedTemporaryFile()
    for line in start_coords:
        start_file.write(line)
    start_file.flush()

    new_coords_file = tempfile.NamedTemporaryFile()
    unmapped_file = tempfile.NamedTemporaryFile()

    subprocess.call(['./liftOver', start_file.name, chain_file, new_coords_file.name, unmapped_file.name])

    new_coords = []
    for line in new_coords_file:
        new_coords.append(line)
    new_coords_file.close()

    unmapped = []
    for line in unmapped_file:
        unmapped.append(line)
    unmapped_file.close()

    res = {'coords': new_coords,
           'unmapped': unmapped}
    return res



if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)

