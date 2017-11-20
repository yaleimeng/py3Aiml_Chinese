'''
一些通用常数, 包括 Python3/Python2 区分对待
'''
import sys

# Package 版本
VERSION = '0.9.1'

# Python 2/3 兼容性
PY3 = sys.version_info[0] == 3
if PY3:
    unicode = str

