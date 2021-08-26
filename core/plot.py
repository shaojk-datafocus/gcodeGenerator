# -*- coding: utf-8 -*-
# @Time    : 2021/8/25 17:12
# @Author  : ShaoJK
# @File    : plot.py
# @Remark  :
import re

from core import parser

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

