# Converts the mongodb JSON dump of the flock presentation proposals to a
# format that is accepted by the Fedora voting application

import json

baseurl = 'http://register.flocktofedora.org'
proposals = []

with file('proposals.json') as f:
    for i, row in enumerate(f):
        row = json.loads(row)
        assert '!' not in row['title'], 'Title contains "!"'
        assert '|' not in row['title'], 'Title contains "|"'
        url = baseurl + '/proposals#%d' % (i + 1)
        proposals.append('%s!%s' % (row['title'], url))

print('|'.join(proposals))
