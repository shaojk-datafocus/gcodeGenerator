# -*- coding: utf-8 -*-
# @Time    : 2021/8/27 11:22
# @Author  : ShaoJK
# @File    : svg.py
# @Remark  :
import re
from xml.etree.ElementTree import Element

from core import path


COMMANDS = set('MmZzLlHhVvCcSsQqTtAa')
UPPERCASE = set('MZLHVCSQTA')

COMMAND_RE = re.compile("([MmZzLlHhVvCcSsQqTtAa])")
FLOAT_RE = re.compile("[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?")

def _tokenize_path(pathdef):
    for x in COMMAND_RE.split(pathdef):
        if x in COMMANDS:
            yield x
        for token in FLOAT_RE.findall(x):
            yield token

class SVGState(object):
    def __init__(self, fill=(0., 0., 0.), fillOpacity=None, fillRule='nonzero', stroke=None, strokeOpacity=None,
                 strokeWidth=0.1, strokeWidthScaling=True):
        self.fill = fill
        self.fillOpacity = fillOpacity
        self.fillRule = fillRule
        self.stroke = stroke
        self.strokeOpacity = strokeOpacity
        self.strokeWidth = strokeWidth
        self.strokeWidthScaling = strokeWidthScaling

    def __repr__(self):
        return 'SVGState(fill=%s, fillOpacity=%s, fillRule=%s, stroke=%s, strokeOpacity=%s, strokeWidth=%s, strokeWidthScaling=%s)' % (
            self.fill, self.fillOpacity, self.fillRule, self.stroke, self.strokeOpacity,self.strokeWidth, self.strokeWidthScaling
        )

    def clone(self):
        return SVGState(fill=self.fill, fillOpacity=self.fillOpacity, fillRule=self.fillRule, stroke=self.stroke,
                        strokeOpacity=self.strokeOpacity,
                        strokeWidth=self.strokeWidth, strokeWidthScaling=self.strokeWidthScaling)

class SVGElement(object):
    def __init__(self, svg:Element, matrix):
        self.svg = svg
        self.tag = re.sub(r'.*}', '', svg.tag).lower()
        self.state = SVGState()
        self.matrix = matrix
        self.paths = []
        self.parseElement()

    def __repr__(self):
        return 'SVGElement(%s, paths=%d, state=%s, matrix=%s)' % (self.tag, len(self.paths), repr(self.state), self.matrix)

    def __iter__(self):
        for path in self.paths:
            yield path

    def parseElement(self):
        # 处理不同的标签
        if self.tag == 'path':
            path = self.parse_path(self.svg.attrib['d'])
            if len(path):
                self.paths.append(path)
        elif self.tag == 'circle':
            path = self.path_from_ellipse(self.getFloatAttribute('cx'), self.getFloatAttribute('cy'), self.getFloatAttribute('r'), self.getFloatAttribute('r'))
            self.paths.append(path)
        elif self.tag == 'ellipse':
            path = self.path_from_ellipse(self.getFloatAttribute('cx'), self.getFloatAttribute('cy'), self.getFloatAttribute('rx'), self.getFloatAttribute('ry'))
            self.paths.append(path)
        elif self.tag == 'line':
            x1 = self.getFloatAttribute('x1')
            y1 = self.getFloatAttribute('y1')
            x2 = self.getFloatAttribute('x2')
            y2 = self.getFloatAttribute('y2')
            p = 'M %.9f %.9f L %.9f %.9f' % (x1,y1,x2,y2)
            path = self.parse_path(p, matrix=self.matrix)
            self.paths.append(path)
        elif self.tag == 'polygon':
            points = re.split(r'[\s,]+', self.svg.attrib['points'].strip())
            p = ' '.join(['M', points[0], points[1], 'L'] + points[2:] + ['Z'])
            path = self.parse_path(p, matrix=self.matrix)
            self.paths.append(path)
        elif self.tag == 'polyline':
            points = re.split(r'[\s,]+', self.svg.attrib['points'].strip())
            p = ' '.join(['M', points[0], points[1], 'L'] + points[2:])
            path = self.parse_path(p, matrix=self.matrix)
            self.paths.append(path)
        elif self.tag == 'rect':
            x = self.getFloatAttribute('x')
            y = self.getFloatAttribute('y')
            w = self.getFloatAttribute('width')
            h = self.getFloatAttribute('height')
            rx = self.getFloatAttribute('rx',default=None)
            ry = self.getFloatAttribute('ry',default=None)
            path = self.path_from_rect(x,y,w,h,rx,ry)
            self.paths.append(path)
        elif self.tag == 'g' or self.tag == 'svg':
            for subElement in self.svg:
                self.paths += SVGElement(subElement,self.matrix).paths # 把子级的paths合并
        # TODO: 目前先不考虑use
        else:
            return None
            raise KeyError('parseElement encounter unknown tag: %s'%self.tag)

    def applyMatrix(self, matrix, z):
        return complex(z.real * matrix[0] + z.imag * matrix[1] + matrix[2],
                       z.real * matrix[3] + z.imag * matrix[4] + matrix[5])
    def scaler(self, p):
        if self.matrix is None:
            return p
        else:
            # matrix[1] = 0  matrix[3] = 0
            # matrix[0] = 画布宽与视窗宽比  matrix[4]= 画布高与视窗高度比的负数
            # matrix[5] =
            return complex(p.real * self.matrix[0] + self.matrix[2], p.imag * self.matrix[4])
            # TODO: 不能理解为什么要使用这个matrix[5], 以及matrix[4]为什么使用负数，应该下文进行旋转的时候有需要
            # 有可能是因为svg的y轴与cnc画图y轴是相反的，需要需要这么操作，不然图像可能会翻转
            return complex(p.real * self.matrix[0] + p.imag * self.matrix[1] + self.matrix[2],
                       p.real * self.matrix[3] + p.imag * self.matrix[4] + self.matrix[5])

    def parse_path(self, pathdef, current_pos=0j):
        # In the SVG specs, initial movetos are absolute, even if
        # specified as 'm'. This is the default behavior here as well.
        # But if you pass in a current_pos variable, the initial moveto
        # will be relative to that current_pos. This is useful.
        elements = list(_tokenize_path(pathdef))
        # Reverse for easy use of .pop()
        elements.reverse()

        segments = path.Path(svgState=self.state)
        start_pos = None
        command = None

        while elements:

            if elements[-1] in COMMANDS: # 如果是命令 # 这里在选定命令
                # New command.
                last_command = command  # Used by S and T
                command = elements.pop()
                absolute = command in UPPERCASE # 大写命令则视为绝对位置
                command = command.upper()
            else: # 如果是数值
                # If this element starts with numbers, it is an implicit command
                # and we don't change the command. Check that it's allowed:
                if command is None:
                    raise ValueError("Unallowed implicit command in %s, position %s" % (
                        pathdef, len(pathdef.split()) - len(elements)))
                last_command = command  # Used by S and T

            if command == 'M':
                # Moveto command.
                x = elements.pop()
                y = elements.pop()
                pos = float(x) + float(y) * 1j
                if absolute:
                    current_pos = pos
                else:
                    current_pos += pos

                # when M is called, reset start_pos
                # This behavior of Z is defined in svg spec:
                # http://www.w3.org/TR/SVG/paths.html#PathDataClosePathCommand
                start_pos = current_pos

                # Implicit moveto commands are treated as lineto commands.
                # So we set command to lineto here, in case there are
                # further implicit commands after this moveto.
                command = 'L'

            elif command == 'Z':
                # Close path
                if current_pos != start_pos:
                    segments.append(path.Line(self.scaler(current_pos), self.scaler(start_pos)))
                if len(segments):
                    segments.closed = True
                current_pos = start_pos
                start_pos = None
                command = None  # You can't have implicit commands after closing.

            elif command == 'L':
                x = elements.pop()
                y = elements.pop()
                pos = float(x) + float(y) * 1j
                if not absolute:
                    pos += current_pos
                segments.append(path.Line(self.scaler(current_pos), self.scaler(pos)))
                current_pos = pos

            elif command == 'H':
                x = elements.pop()
                pos = float(x) + current_pos.imag * 1j
                if not absolute:
                    pos += current_pos.real
                segments.append(path.Line(self.scaler(current_pos), self.scaler(pos)))
                current_pos = pos

            elif command == 'V':
                y = elements.pop()
                pos = current_pos.real + float(y) * 1j
                if not absolute:
                    pos += current_pos.imag * 1j
                segments.append(path.Line(self.scaler(current_pos), self.scaler(pos)))
                current_pos = pos

            elif command == 'C':
                control1 = float(elements.pop()) + float(elements.pop()) * 1j
                control2 = float(elements.pop()) + float(elements.pop()) * 1j
                end = float(elements.pop()) + float(elements.pop()) * 1j

                if not absolute:
                    control1 += current_pos
                    control2 += current_pos
                    end += current_pos

                segments.append(path.CubicBezier(self.scaler(current_pos), self.scaler(control1), self.scaler(control2), self.scaler(end)))
                current_pos = end

            elif command == 'S':
                # Smooth curve. First control point is the "reflection" of
                # the second control point in the previous path.

                if last_command not in 'CS':
                    # If there is no previous command or if the previous command
                    # was not an C, c, S or s, assume the first control point is
                    # coincident with the current point.
                    control1 = self.scaler(current_pos)
                else:
                    # The first control point is assumed to be the reflection of
                    # the second control point on the previous command relative
                    # to the current point.
                    control1 = 2 * self.scaler(current_pos) - segments[-1].control2

                control2 = float(elements.pop()) + float(elements.pop()) * 1j
                end = float(elements.pop()) + float(elements.pop()) * 1j

                if not absolute:
                    control2 += current_pos
                    end += current_pos

                segments.append(path.CubicBezier(self.scaler(current_pos), control1, self.scaler(control2), self.scaler(end)))
                current_pos = end

            elif command == 'Q':
                control = float(elements.pop()) + float(elements.pop()) * 1j
                end = float(elements.pop()) + float(elements.pop()) * 1j

                if not absolute:
                    control += current_pos
                    end += current_pos

                segments.append(path.QuadraticBezier(self.scaler(current_pos), self.scaler(control), self.scaler(end)))
                current_pos = end

            elif command == 'T':
                # Smooth curve. Control point is the "reflection" of
                # the second control point in the previous path.

                if last_command not in 'QT':
                    # If there is no previous command or if the previous command
                    # was not an Q, q, T or t, assume the first control point is
                    # coincident with the current point.
                    control = self.scaler(current_pos)
                else:
                    # The control point is assumed to be the reflection of
                    # the control point on the previous command relative
                    # to the current point.
                    control = 2 * self.scaler(current_pos) - segments[-1].control

                end = float(elements.pop()) + float(elements.pop()) * 1j

                if not absolute:
                    end += current_pos

                segments.append(path.QuadraticBezier(self.scaler(current_pos), control, self.scaler(end)))
                current_pos = end

            elif command == 'A':
                radius = float(elements.pop()) + float(elements.pop()) * 1j
                rotation = float(elements.pop())
                arc = float(elements.pop())
                sweep = float(elements.pop())
                end = float(elements.pop()) + float(elements.pop()) * 1j

                if not absolute:
                    end += current_pos

                segments.append(path.Arc(current_pos, radius, rotation, arc, sweep, end, self.scaler))
                current_pos = end

        return segments
    
    def path_from_ellipse(self, x, y, rx, ry):
        arc = "M %.9f %.9f " % (x - rx, y)
        arc += "A %.9f %.9f 0 0 1 %.9f %.9f " % (rx, ry, x + rx, y)
        arc += "A %.9f %.9f 0 0 1 %.9f %.9f" % (rx, ry, x - rx, y)
        return self.parse_path(arc)

    def path_from_rect(self, x, y, w, h, rx, ry):
        if not rx and not ry:
            rect = "M %.9f %.9f h %.9f v %.9f h %.9f Z" % (x, y, w, h, -w)
        else:
            if rx is None:
                rx = ry
            elif ry is None:
                ry = rx
            rect = "M %.9f %.9f h %.9f " % (x + rx, y, w - 2 * rx)
            rect += "a %.9f %.9f 0 0 1 %.9f %.9f " % (rx, ry, rx, ry)
            rect += "v %.9f " % (h - 2 * ry)
            rect += "a %.9f %.9f 0 0 1 %.9f %.9f " % (rx, ry, -rx, ry)
            rect += "h %.9f " % -(w - 2 * rx)
            rect += "a %.9f %.9f 0 0 1 %.9f %.9f " % (rx, ry, -rx, -ry)
            rect += "v %.9f " % -(h - 2 * ry)
            rect += "a %.9f %.9f 0 0 1 %.9f %.9f Z" % (rx, ry, rx, -ry)
        return self.parse_path(rect, matrix=matrix)

    def getFloatAttribute(self, attribute,default=0.):
        try:
            return float(self.svg.attrib[attribute].strip())
        except KeyError:
            return default
