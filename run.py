# -*- coding: utf-8 -*-
# @Time    : 2021/8/20 15:27
# @Author  : ShaoJK
# @File    : run.py
# @Remark  :
import sys

import config
import xml.etree.ElementTree as ET
from gcodeplot.gcodeplot import Plotter, Pen, parseSVG, removePenBob, dedup, directionalize, describePen, emitGcode
from gcodeplot.svgpath.parser import rgbFromColor
from gcodeplot.svgpath.shader import Shader

from gcodeplot.gcodeplotutils.processoffset import OffsetProcessor

shader = Shader()
plotter = Plotter()
pens = {1: Pen('1 (0.,0.) black default')}

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

# 读取数据
with open(config.SVG_PATH) as f:
    data = f.read()
# 解析SVG
svgTree = ET.fromstring(data)
if not 'svg' in svgTree.tag:
    svgTree = None
assert svgTree, "从文件中未解析到svg标签"
penData = parseSVG(svgTree,
                   tolerance=config.general.tolerance,
                   shader=shader,
                   strokeAll=config.strokeAll,
                   pens=pens,
                   extractColor=rgbFromColor(config.fitting.extractColor))

penData = removePenBob(penData)

op = OffsetProcessor(toolOffset=config.cutting.toolOffset, overcut=config.cutting.overcut, tolerance=config.general.tolerance)
for pen in penData:
    penData[pen] = op.processPath(penData[pen])

for pen in penData:
    penData[pen] = directionalize(penData[pen], config.drawing.direction)
penData = removePenBob(penData)

print(len(penData))

align = [0,0]
scalingMode = 0 # SCALE_NONE
gcodePause = '@pause'
pauseAtStart = False
svgSimulation = False
g = emitGcode(penData, align=align, scalingMode=scalingMode, tolerance=config.general.tolerance,
                plotter=plotter, gcodePause=gcodePause, pens=pens, pauseAtStart=pauseAtStart, simulation=svgSimulation)

print(g)