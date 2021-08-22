# -*- coding: utf-8 -*-
# @Time    : 2021/8/20 14:40
# @Author  : ShaoJK
# @File    : config.py.py
# @Remark  :
from utils import Dict


general = Dict()
general.toolMode = 'draw'
general.tolerance = 0.05 # float
general.minX = 0
general.minY = 0
general.maxX = 200
general.maxY = 200
general.workZ = 15
general.liftDeltaZ = 4
general.safeDeltaZ = 20
general.penUpSpeed = 40
general.penDownSpeed = 35
general.zSpeed = 5
general.sendAndSave = ''
general.sendSpeed = 115200

fitting = Dict()
fitting.scale = 'none'
fitting.alignX = 'none'
fitting.alignY = 'none'
fitting.extractColor = 'black' # string 16进制rgb

drawing = Dict()
drawing.shadingThreshold = 1
drawing.shadingLightest = 3
drawing.shadingDarkest = 0.5
drawing.shadingAngle = 45
drawing.booleanShadingCrosshatch = 0
drawing.optimizationTime = 60
drawing.direction = 45

cutting = Dict()
cutting.toolOffset = 0
cutting.overcut = 1
cutting.booleanSort = 1
cutting.liftCommand = ''
cutting.downCommand = ''

# 以下配置是脚本中的默认值
# SVG_PATH = "test.svg"
SVG_PATH = "icon_bilibili-square.svg"
strokeAll = False