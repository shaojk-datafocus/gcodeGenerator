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


code = ["G00 S1; endstops|",
       "G00 E0; no extrusion|",
       "G01 S1; endstops|",
       "G01 E0; no extrusion|",
       "G21; millimeters|",
       "G91 G0 F%.1f{{zspeed*60}} Z%.3f{{safe}}; pen park !!Zsafe|",
       "G90; absolute|",
       "G28 X; home|",
       "G28 Y; home|",
       "G28 Z; home"]
for c in code:
    print(re.findall(r'\{\{([^}]+)\}\}',c))