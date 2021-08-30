# -*- coding: utf-8 -*-
# @Time    : 2021/8/20 15:27
# @Author  : ShaoJK
# @File    : run.py
# @Remark  :
import sys

import config
import xml.etree.ElementTree as ET

from core.gcode import emitGcode
from core.plot import Plotter, Pen
from core.parser import parseSVG, rgbFromColor
from core.process import removePenBob, dedup
from core.shader import Shader
from gcodeplot.gcodeplotutils.processoffset import OffsetProcessor

shader = Shader()
plotter = Plotter()

# 初始化Plotter
plotter.xyMin = (config.general.minX,plotter.xyMin[1])
plotter.xyMin = (plotter.xyMin[0],config.general.minY)
plotter.xyMax = (config.general.maxX,plotter.xyMax[1])
plotter.xyMax = (plotter.xyMax[0],config.general.maxY)
plotter.liftDeltaZ = config.general.liftDeltaZ
plotter.workZ = config.general.workZ
plotter.safeDeltaZ = config.general.safeDeltaZ
plotter.zSpeed = config.general.zSpeed
plotter.updateVariables()

# 初始化shader
shader.unshadedThreshold = config.drawing.shadingThreshold
shader.lightestSpacing = config.drawing.shadingLightest
shader.darkestSpacing = config.drawing.shadingDarkest
shader.angle = config.drawing.shadingAngle
shader.crossHatch = config.drawing.booleanShadingCrosshatch
shader.setDrawingDirectionAngle(config.drawing.direction)

def parseData(penData):
    for path in penData:
        for point in path:
            print("%f, %f"%point)

# 读取数据
with open(config.SVG_PATH, encoding='utf-8') as f:
    data = f.read()
# 解析SVG
svgTree = ET.fromstring(data)
if not 'svg' in svgTree.tag:
    svgTree = None
assert svgTree, "从文件中未解析到svg标签"

data = plotter.parseSVG(svgTree,
                        tolerance=config.general.tolerance,
                        shader=shader,
                        strokeAll=config.strokeAll,
                        extractColor=rgbFromColor(config.fitting.extractColor))
# print(data)
exit(0)
data = removePenBob(data) # 合并同起点终点的路径

# data = dedup(data) # 这个什么也没变

# for pen in penData:
#     penData[pen] = directionalize(penData[pen], config.drawing.direction)
# penData = removePenBob(penData)
align = [0,0]
scalingMode = 0 # SCALE_NONE
gcodePause = '@pause'
gcode = emitGcode(data, align=align, scalingMode=scalingMode, tolerance=config.general.tolerance,
                plotter=plotter, gcodePause=gcodePause)

# for g in gcode:
#     print(g)
with open("output.gcode", "w") as f:
    for g in gcode:
        f.write(g+"\n")
