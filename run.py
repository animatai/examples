#!./venv3/bin/python
# pylint: disable=missing-docstring, exec-used, invalid-name
import sys

mod = sys.argv[1]
num = sys.argv[2] if len(sys.argv) >= 3 else '100'
seed = sys.argv[3] if len(sys.argv) >= 4 else 'None'
s = 'import ' + mod
s += '\n' + mod + '.run(None, ' + num + ', ' + seed + ')'


print('Generated python:\n'+s+'\n')

exec(s)
