# -*- coding: utf-8 -*-
# @Time    : 2021/8/25 17:12
# @Author  : ShaoJK
# @File    : plot.py
# @Remark  :
import re

from core import parser
from core.shader import Shader
from core.svg import SVGElement
from core.utils import sizeFromString, isSameColor

SCALE_NONE = 0
SCALE_DOWN_ONLY = 1
SCALE_FIT = 2
ALIGN_NONE = 0
ALIGN_BOTTOM = 1
ALIGN_TOP = 2
ALIGN_LEFT = ALIGN_BOTTOM
ALIGN_RIGHT = ALIGN_TOP
ALIGN_CENTER = 3

class Plotter(object):
    def __init__(self, xyMin=(7, 8), xyMax=(204, 178),
                 drawSpeed=35, moveSpeed=40, zSpeed=5, workZ=14.5, liftDeltaZ=2.5, safeDeltaZ=20,
                 liftCommand=None, safeLiftCommand=None, downCommand=None, comment=";",
                 initCode="G00 S1; endstops|"
                          "G00 E0; no extrusion|"
                          "G01 S1; endstops|"
                          "G01 E0; no extrusion|"
                          "G21; millimeters|"
                          "G91 G0 F%.1f{{zspeed*60}} Z%.3f{{safe}}; pen park !!Zsafe|"
                          "G90; absolute|"
                          "G28 X; home|"
                          "G28 Y; home|"
                          "G28 Z; home",
                 endCode=None):
        self.xyMin = xyMin
        self.xyMax = xyMax
        self.drawSpeed = drawSpeed
        self.moveSpeed = moveSpeed
        self.workZ = workZ
        self.liftDeltaZ = liftDeltaZ
        self.safeDeltaZ = safeDeltaZ
        self.zSpeed = zSpeed
        self.liftCommand = liftCommand
        self.safeLiftCommand = safeLiftCommand
        self.downCommand = downCommand
        self.initCode = initCode
        self.endCode = endCode
        self.comment = comment
        self.paths = []

    def inRange(self, point):
        for i in range(2):
            if point[i] < self.xyMin[i] - .001 or point[i] > self.xyMax[i] + .001:
                return False
        return True

    @property
    def safeUpZ(self):
        return self.workZ + self.safeDeltaZ

    @property
    def penUpZ(self):
        return self.workZ + self.liftDeltaZ

    def updateVariables(self):
        self.variables = {'lift': self.liftDeltaZ, 'work': self.workZ, 'safe': self.safeDeltaZ, 'left': self.xyMin[0],
                          'bottom': self.xyMin[1], 'zspeed': self.zSpeed, 'movespeed': self.moveSpeed}
        self.formulas = {'right': str(self.xyMax[0]), 'top': str(self.xyMax[1]), 'up': 'work+lift', 'park': 'work+safe',
                         'centerx': '(left+right)/2.', 'centery': '(top+bottom)/2.'}

    def parseSVG(self, svg, tolerance=0.05, shader=None, strokeAll=False, extractColor=None):
        data = []
        for path in self.getPathsFromSVG(svg):
            lines = []

            stroke = strokeAll or (path.svgState.stroke is not None and (
                        extractColor is None or isSameColor(path.svgState.stroke, extractColor)))
            # stroke = True
            # TODO: 目前先不考虑不同颜色笔的情况，因为绘图仪目前没有这个功能
            for line in path.linearApproximation(error=tolerance):  # 返回一个Path对象，里面是经过直线化和共线合并处理的Line对象
                if stroke:
                    data.append([(line.start.real, line.start.imag), (line.end.real, line.end.imag)])
                lines.append((line.start, line.end))  # lines又存储成了线段的端点组
            print(lines)
            # 需要svg的path的fill属性不为空，并且指定的提取颜色与填充颜色一致才会执行Shader操作
            if shader is not None and shader.isActive() and path.svgState.fill is not None and (extractColor is None or
                                                                                                isSameColor(
                                                                                                    path.svgState.fill,
                                                                                                    extractColor)):
                grayscale = sum(path.svgState.fill) / 3.  # 计算灰度，灰度相当于图片的亮度图
                mode = Shader.MODE_NONZERO if path.svgState.fillRule == 'nonzero' else Shader.MODE_EVEN_ODD
                # mode = 1 # nonzero
                if path.svgState.fillOpacity is not None:  # fillOpacity是None
                    grayscale = grayscale * path.svgState.fillOpacity + 1. - path.svgState.fillOpacity  # TODO: real alpha!
                # avoidOutline 是False
                # lines是直线化处理后线段的端点组列表
                fillLines = shader.shade(lines, grayscale, mode=mode)
                # fillLines 是填充线
                for line in fillLines:
                    data.append([(line[0].real, line[0].imag), (line[1].real, line[1].imag)])
                # 仅保留填充线？原先的轮廓线不管了？
            else:
                for line in lines:
                    data.append([(line[0].real, line[0].imag), (line[1].real, line[1].imag)])

        return data

    def getPathsFromSVG(self,svg) -> SVGElement:
        # 先获取svg整体的基础信息
        width = sizeFromString(svg.attrib['width'].strip())
        height = sizeFromString(svg.attrib['height'].strip())
        viewBox = list(map(float, re.split(r'[\s,]+', svg.attrib['viewBox'].strip())))
        # viewBox(x0,y0,x1,y1)

        viewBoxWidth = viewBox[2]
        viewBoxHeight = viewBox[3]

        viewBox[2] += viewBox[0] # x轴
        viewBox[3] += viewBox[1] # y轴

        matrix = [width / viewBoxWidth, 0, -viewBox[0] * width / viewBoxWidth,
                  0, height / viewBoxHeight, viewBox[3] * height / viewBoxHeight]
        # 递归遍历所有图层，获取path
        # self.getPaths(matrix, svg)
        return SVGElement(svg, matrix)

class Pen(object):
    def __init__(self, text):
        text = re.sub(r'\s+', r' ', text.strip())
        self.description = text
        data = text.split(' ', 4)
        if len(data) < 3:
            raise ValueError('Pen parsing error')
        if len(data) < 4:
            data.append('')
        self.pen = int(data[0])
        self.offset = tuple(map(float, re.sub(r'[()]', r'', data[1]).split(',')))
        self.color = parser.rgbFromColor(data[2])
        self.name = data[3]

class Scale(object):
    def __init__(self, scale=(1., 1.), offset=(0., 0.)):
        self.offset = offset
        self.scale = scale

    def clone(self):
        return Scale(scale=[self.scale[0], self.scale[1]], offset=[self.offset[0], self.offset[1]])

    def __repr__(self):
        return str(self.scale) + ',' + str(self.offset)

    def fit(self, plotter, xyMin, xyMax):
        s = [0, 0]
        o = [0, 0]
        for i in range(2):
            delta = xyMax[i] - xyMin[i]
            if delta == 0:
                s[i] = 1.
            else:
                s[i] = (plotter.xyMax[i] - plotter.xyMin[i]) / delta
        self.scale = [min(s), min(s)]
        self.offset = list(plotter.xyMin[i] - xyMin[i] * self.scale[i] for i in range(2))

    def align(self, plotter, xyMin, xyMax, align):
        o = [0, 0]
        for i in range(2):
            if align[i] == ALIGN_LEFT:
                o[i] = plotter.xyMin[i] - self.scale[i] * xyMin[i]
            elif align[i] == ALIGN_RIGHT:
                o[i] = plotter.xyMax[i] - self.scale[i] * xyMax[i]
            elif align[i] == ALIGN_NONE:
                o[i] = self.offset[i]  # self.xyMin[i]
            elif align[i] == ALIGN_CENTER:
                o[i] = 0.5 * (plotter.xyMin[i] - self.scale[i] * xyMin[i] + plotter.xyMax[i] - self.scale[i] * xyMax[i])
            else:
                raise ValueError()
        self.offset = o

    def scalePoint(self, point):
        return (point[0] * self.scale[0] + self.offset[0], point[1] * self.scale[1] + self.offset[1])

def processCode(code, plotter):
    if not code:
        return []

    pattern = r'\{\{([^}]+)\}\}'  # 获取{{ }}的标识，

    data = tuple(evaluate(expr, plotter.variables, plotter.formulas) for expr in re.findall(pattern, code))
    # evaluate是将命令中一些规定的语句转换成具体数值

    formatString = re.sub(pattern, '', code.replace('|', '\n'))

    return [formatString % data]

SAFE_EVAL_RE = re.compile(r'^[-+/*()eE0-9.]+$')

def safeEval(string):
    if not SAFE_EVAL_RE.match(string):
        raise ValueError()
    return eval(string)

def evaluate(value, variables, formulas, MAX_DEPTH=100):
    tryAgain = True
    depth = 0
    while tryAgain and depth < MAX_DEPTH:
        tryAgain = False
        for x in formulas:
            value, n = re.subn(r'\b' + x + r'\b', '(' + formulas[x] + ')', value)
            if n > 0: tryAgain = True
        for x in variables:
            value, n = re.subn(r'\b' + x + r'\b', repr(variables[x]), value)
            if n > 0: tryAgain = True
        depth += 1
    if depth >= MAX_DEPTH:
        raise ValueError()
    return safeEval(value)

def gcodeHeader(plotter):
    return processCode(plotter.initCode, plotter)

