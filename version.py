import re
import subprocess

VERSION = None


def _get_version():
    '''return either the tag on HEAD or the shortened commit id if not found'''
    out = subprocess.check_output(['git', 'log', '--format=%h %d', '-1'])
    version, ref_names = out.split('(')
    m = re.match(r'.*tag: (\d{4}\.\d{2}.*?),', ref_names)
    if m:
        version = m.group(1)
    return version.strip()

try:
    VERSION = _get_version()
except:
    VERSION = '???'
