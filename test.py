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
from gcodeplot.svgpath.path import approximate


points = approximate(self, 0., 1., self.point(0.), self.point(1.), error, 0, max_depth)