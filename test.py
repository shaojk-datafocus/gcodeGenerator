# # -*- coding: utf-8 -*-
# # @Time    : 2021/8/20 14:42
# # @Author  : ShaoJK
# # @File    : test.py
# # @Remark  :
#
# import xml.etree.ElementTree as ET
#
# with open("gcodeplot/gcodeplot.inx", "r") as f:
#     data = f.read()
# xml = ET.fromstring(data)
#
# page = None
# for ele in xml.iter():
#     # if hasattr(ele,'name'):
#     #     print(ele.name)
#     e = dict(ele.items())
#     if 'name' in e.keys():
#         if "page" in ele.tag:
#             page = e['name']
#             print(page)
#         else:
#             print("%s.%s"%(page,e['name']))


# a = complex(1,1)
#
# print(a)
# b = complex(0.5,0.5)
#
# print(a+b)
# print(a-b)
# print(a*b)
# print(a/b)

import re

# code = "m 13.015936,12.227092 0,100 100,0 0,-100 z"
#
# result = re.compile("([MmZzLlHhVvCcSsQqTtAa])").split(code)
# print(result)

v = complex(3,5)
print(type(v.imag))