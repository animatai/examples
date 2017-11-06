#!./venv3/bin/python
# pylint: disable=missing-docstring, exec-used, invalid-name
import sys

mod = sys.argv[1]
num = sys.argv[2] if len(sys.argv) >= 3 else '100'
seed = sys.argv[3] if len(sys.argv) >= 4 else 'None'
trials = sys.argv[4] if len(sys.argv) >= 5 else '1'
s = 'import ' + mod
s += '\n' + mod + '.run(None, ' + num + ', ' + seed + ', ' + trials + ')'


print('Generated python:\n'+s+'\n')

exec(s)
