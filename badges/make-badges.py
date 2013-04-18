import csv
from pprint import pprint
import re
import subprocess

RE_GET_WIDTH = re.compile('<svg width="([0-9]*)" height=.*')

def build_barcode_svg(data):
    if data['fas id']:
        mecard = ('MECARD:N:%(last name)s,%(first name)s;'
                  'EMAIL:%(fas id)s@fedoraproject.org;'
                  'URL:http://fedoraproject.org/wiki/User:%(fas id)s;;') % data
    else:
        mecard = 'MECARD:N:%(last name)s,%(first name)s;;' % data
    command = ['zint', '--directsvg', '-b', '58', '-d', mecard]
    xml = subprocess.Popen(command, stdout=subprocess.PIPE).stdout.read()
    xml_lines = xml.splitlines()
    width = int(RE_GET_WIDTH.match(xml_lines[3]).group(1))
    rects = []
    for line in xml_lines:
        if '<rect' in line:
            rects.append(line.strip())
    factor = 101.25 / width
    return ('\n'.join(rects), factor)

def xml_filter(string):
    string = string.replace('&', '&amp;')
    string = string.replace('<', '&lt;')
    return string

if __name__ == '__main__':
    page_template = file('badge-template.svg').read().replace('%;', '%%;')

    csv_file = file('badges.csv')
    badge_info = csv.DictReader(csv_file)

    pages = []
    i = 0
    this_page = {}
    for row in badge_info:
        i += 1
        this_page['firstname%d' % i] = xml_filter(row['first name'])
        this_page['lastname%d' % i] = xml_filter(row['last name'])
        this_page['tagline%d' % i] = xml_filter(row['comment'])
        if row['veg code'] and row['shirt size']:
            grayinfo = '%s / %s' % (row['shirt size'], row['veg code'])
        elif row['shirt size']:
            grayinfo = row['shirt size']
        elif row['veg code']:
            grayinfo = row['veg code']
        else:
            grayinfo = ''
        this_page['grayinfo%d' % i] = xml_filter(grayinfo)
        (this_page['barcode%d' % i], this_page['barcodescale%d' % i]) = \
                build_barcode_svg(row)
        if i is 6:
            pages.append(this_page)
            i = 0
            this_page = {}
    if i is not 6:
        for i in range(i+1, 7):
            this_page['firstname%d' % i] = ''
            this_page['lastname%d' % i] = ''
            this_page['tagline%d' % i] = ''
            this_page['grayinfo%d' % i] = ''
            this_page['barcode%d' % i] = ''
            this_page['barcodescale%d' % i] = 0
        pages.append(this_page)

    i = 0
    for page in pages:
        i += 1
        svg = page_template % page
        file('page-%02d.svg' % i, 'w').write(svg)
        command = ['inkscape', '-z', '-A', 'page-%02d.pdf' % i, '-C',
                   '/dev/stdin']
        print command
        process = subprocess.Popen(command, stdin=subprocess.PIPE)
        process.communicate(svg)
