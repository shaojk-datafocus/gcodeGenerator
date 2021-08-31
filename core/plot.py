# -*- coding: utf-8 -*-
# @Time    : 2021/8/25 17:12
# @Author  : ShaoJK
# @File    : plot.py
# @Remark  :
import re
import json
import math

from core import parser
from core.shader import Shader
from core.svg import SVGElement
from core.utils import sizeFromString, isSameColor
from core.path import Point, Hatchline

SCALE_NONE = 0
SCALE_DOWN_ONLY = 1
SCALE_FIT = 2
ALIGN_NONE = 0
ALIGN_BOTTOM = 1
ALIGN_TOP = 2
ALIGN_LEFT = ALIGN_BOTTOM
ALIGN_RIGHT = ALIGN_TOP
ALIGN_CENTER = 3

def compute_distance(a, b):
    return math.hypot(b.x-a.x, b.y-a.y)

class Plotter(object):
    def __init__(self, xyMin=(7, 8), xyMax=(204, 178),
                 drawSpeed=35, moveSpeed=40, zSpeed=5, workZ=14.5, liftDeltaZ=2.5, safeDeltaZ=20,
                 liftCommand=None, safeLiftCommand=None, downCommand=None, comment=";",
                 initCode="G00 S1; endstops|"
                          "G21; millimeters|"
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
            print(path)
            for line in path.linearApproximation(error=tolerance):  # 返回一个Path对象，里面是经过直线化和共线合并处理的Line对象
                if stroke:
                    data.append([(line.start.x, line.start.y), (line.end.x, line.end.y)])
                lines.append((line.start, line.end))  # lines又存储成了线段的端点组
            # lines 多边形的线段 [4, 2, 2]
            angleDegrees = 45
            spacing = 3
            deltaY = spacing / 2
            # 使用旋转变换，变换各点的坐标
            # 构造变换矩阵
            # rotate = complex(math.cos(angleDegrees * math.pi / 180.), math.sin(angleDegrees * math.pi / 180.))
            cos = math.cos(angleDegrees * math.pi / 180)
            sin = math.sin(angleDegrees * math.pi / 180)
            rotate_matrix = [[cos, sin], [-sin, cos]]
            rotate_inverse_matrix = [[cos, -sin], [sin, cos]] # 逆时针旋转
            # polygon = [(line[0] / rotate, line[1] / rotate) for line in lines]  # 所有的点逆时针旋转45度
            polygon = [(line[0].transform(rotate_matrix), line[1].transform(rotate_matrix)) for line in lines]

            # 获取图形Y轴的范围
            minY = min(min(line[0].y, line[1].y) for line in polygon)
            maxY = max(max(line[0].y, line[1].y) for line in polygon)

            # 遍历整个y轴范围
            hatchlines = []
            y = minY + deltaY
            maxBatch = 1
            while y < maxY:
                # for 遍历所有多边形线段:
                intersections = []
                for line in polygon:
                    start = line[0]
                    end = line[1]
                    if end.y == y or start.y == y:
                        # 如果hatchline正好经过多边形的端点，那就忽略
                        break
                    # y已知，计算出x，得到交点坐标
                    if end.y < y < start.y or start.y < y < end.y:  # 如果当前填充线y在线段之间
                        if end.x == start.x:  # 如果该线段是竖直的, 在当前线段上放一个点，并记录点在线段起始点的上方还是下方
                            # intersections.append((complex(start.real, y), start.imag < y, line))  # ∵tant90° 不存在
                            intersections.append(Point(start.x,y))
                        else:  # 如果线段不是竖直的
                            k = (end.y - start.y) / (end.x - start.x) # 计算边的斜率
                            # k * (x - z.real) = y - z.imag
                            # so: x = (y - z.imag) / k + z.real
                            # 求线段上的一个点[x, y](y已知)，使点在线段内
                            intersections.append(Point((y-start.y)/k+start.x,y))
                    # hatchline排序、去重
                    intersections.sort(key=lambda p: p.x)
                maxBatch = max(maxBatch, len(intersections)/2)
                hatchlines.append(intersections)
                y += spacing
            # 分组合并
            hatchlinesBatchly = []
            for i in range(int(maxBatch)):
                lines = []
                for hatchline in hatchlines:
                    if len(hatchline) > 2*i:
                        line = Hatchline(*hatchline[2*i:2*i+2])
                        # 逆变换变回原坐标系
                        line.start.transform(rotate_inverse_matrix)
                        line.end.transform(rotate_inverse_matrix)
                        lines.append(line)
                # lines.sort(key=lambda l: l[0].y) # 按照Y轴排序
                hatchlinesBatchly.append(lines)
            # hatchline连笔分组
            j = 0
            while j < len(hatchlinesBatchly):
                hatchlines = hatchlinesBatchly[j]
                last_end = hatchlines[0].end
                i = 1
                while i < len(hatchlines): # 每组hatchline应该是可练笔的
                    hatchline = hatchlines[i]
                    d_start = compute_distance(last_end, hatchline.start)
                    d_end = compute_distance(last_end, hatchline.end)
                    if d_start > d_end:
                        hatchline.reverse()
                        d_start = d_end
                    if d_start > spacing*2: # 如果连笔点距离超出距离，就开启新线段
                        # hatchlinesBatchly.append(hatchlines[i:])
                        hatchlinesBatchly.insert(j+1,hatchlines[i:])
                        hatchlinesBatchly[j] = hatchlines[:i]
                        break
                    else:
                        hatchlines.insert(i, Hatchline(last_end, hatchline.start))
                        last_end = hatchline.end
                        i += 2
                j += 1
            # 将原多边行边框加入
            border = []
            for line in polygon:
                p1 = Point(line[0].real, line[0].imag)
                p2 = Point(line[1].real, line[1].imag)
                p1.transform(rotate_inverse_matrix)
                p2.transform(rotate_inverse_matrix)
                border.append(Hatchline(p1,p2))
            hatchlinesBatchly.insert(0, border)
            data += hatchlinesBatchly
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

        # matrix = [width / viewBoxWidth, 0, -viewBox[0] * width / viewBoxWidth,
        #           0, height / viewBoxHeight, viewBox[3] * height / viewBoxHeight]

        matrix = [[width / viewBoxWidth, 0],
                  [0, height / viewBoxHeight]]

        # matrix[0] = 2
        # matrix[4] = -2
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

