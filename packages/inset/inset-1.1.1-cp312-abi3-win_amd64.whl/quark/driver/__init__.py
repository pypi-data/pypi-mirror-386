# MIT License

# Copyright (c) 2021 YL Feng

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""
Abstract: about driver
    all drivers should be placed in path/to/dev
"""

from .common import BaseDriver, Quantity, compress, decompress, newcfg

try:
    # import URL from dev in systemq
    try:
        # from dev import URL
        URL = 'Not Found'
    except ImportError as e:
        from dev import URL
except Exception as e:
    URL = 'Not Found'


# import json
# import sys
# import zipfile
# from pathlib import Path

# import requests

# try:
#     root = Path(__file__).parents[1]

#     with open(root/'etc/bootstrap.json') as f:
#         ext = json.loads(f.read())['extentions']

#     for module, file in ext['modules'].items():
#         driver = root / f'dev/zipped/{file}'
#         driver.parent.mkdir(exist_ok=True, parents=True)

#         if not driver.exists():
#             location = f"{ext['server']}/packages/dev/{file}"
#             print(f'Trying to download driver from {location}')
#             resp = requests.get(location)

#             with open(driver, 'wb') as f:
#                 f.write(resp.content)
#                 print(f'{location} saved to {driver}')

#             with zipfile.ZipFile(driver) as f:
#                 for zf in f.filelist:
#                     if not zf.filename.startswith(('__MAC', 'dev/__init__')):
#                         # print(zf.filename)
#                         f.extract(zf, driver.parent)

#             if str(driver) not in sys.path:
#                 sys.path.append(str(driver))

#     URL = "https://gitee.com/quarkstudio/iptable/edit/master/iptable.json"
# except Exception as e:
#     print('failed to init dev', e)
