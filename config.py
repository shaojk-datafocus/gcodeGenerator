# -*- coding: utf-8 -*-
# @Time    : 2021/8/20 14:40
# @Author  : ShaoJK
# @File    : config.py.py
# @Remark  :
from easydict import EasyDict

general = EasyDict()
general.toolMode = 'draw'
general.tolerance = 0.05 # float
general.minX = 0
general.minY = 0
general.maxX = 400
general.maxY = 400
general.workZ = 15
general.liftDeltaZ = 4
general.safeDeltaZ = 20
general.penUpSpeed = 40
general.penDownSpeed = 35
general.zSpeed = 5
general.sendAndSave = ''
general.sendSpeed = 115200

fitting = EasyDict()
fitting.scale = 'none'
fitting.alignX = 'none'
fitting.alignY = 'none'
fitting.extractColor = 'black' # string 16进制rgb

drawing = EasyDict()
drawing.shadingThreshold = 1
drawing.shadingLightest = 3
drawing.shadingDarkest = 0.5
drawing.shadingAngle = 45
drawing.booleanShadingCrosshatch = 0
drawing.optimizationTime = 60
drawing.direction = 45

cutting = EasyDict()
cutting.toolOffset = 0
cutting.overcut = 1
cutting.booleanSort = 1
cutting.liftCommand = ''
cutting.downCommand = ''

# 以下配置是脚本中的默认值
# SVG_PATH = "svg/test.svg"
# SVG_PATH = "svg/path.svg"
SVG_PATH = "svg/ellipse.svg"
SVG_PATH = "svg/text.svg"
SVG_PATH = "svg/love.svg"
# SVG_PATH = "svg/bilibili.svg"
strokeAll = False