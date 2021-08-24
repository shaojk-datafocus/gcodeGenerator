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
import math
angleDegrees = 45
# rotate = complex(math.cos(angleDegrees * math.pi / 180.), math.sin(angleDegrees * math.pi / 180.))
rotate = 1+1j
print(rotate)
line = ((1+1j), (0+1j), (1+0j))
print(*line)
print(line[0]/rotate,line[1]/rotate,line[2]/rotate)
print(line[0]*rotate,line[1]*rotate,line[2]*rotate)