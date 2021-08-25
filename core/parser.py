# SVG Path specification parser

import re
from . import path
import xml.etree.ElementTree as ET
import re
import math

from .shader import Shader
from .utils import isSameColor, rgbFromColor

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

def applyMatrix(matrix, z):
    return complex(z.real * matrix[0] + z.imag * matrix[1] + matrix[2], 
             z.real * matrix[3] + z.imag * matrix[4] + matrix[5] )
             
def matrixMultiply(matrix1, matrix2):
    if matrix1 is None:
        return matrix2
    elif matrix2 is None:
        return matrix1
        
    m1 = [matrix1[0:3], matrix1[3:6] ] # don't need last row
    m2 = [matrix2[0:3], matrix2[3:6], [0,0,1]]

    out = []
    
    for i in range(2):
        for j in range(3):
            out.append( sum(m1[i][k]*m2[k][j] for k in range(3)) )
            
    return out

def parse_path(pathdef, current_pos=0j, matrix = None, svgState=None):
    if matrix is None:
        scaler=lambda z : z
    else:
        scaler=lambda z : applyMatrix(matrix, z)
    if svgState is None:
        svgState = path.SVGState()

    # In the SVG specs, initial movetos are absolute, even if
    # specified as 'm'. This is the default behavior here as well.
    # But if you pass in a current_pos variable, the initial moveto
    # will be relative to that current_pos. This is useful.
    elements = list(_tokenize_path(pathdef))
    # Reverse for easy use of .pop()
    elements.reverse()

    segments = path.Path(svgState = svgState)
    start_pos = None
    command = None

    while elements:

        if elements[-1] in COMMANDS:
            # New command.
            last_command = command  # Used by S and T
            command = elements.pop()
            absolute = command in UPPERCASE
            command = command.upper()
        else:
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
                segments.append(path.Line(scaler(current_pos), scaler(start_pos)))
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
            segments.append(path.Line(scaler(current_pos), scaler(pos)))
            current_pos = pos

        elif command == 'H':
            x = elements.pop()
            pos = float(x) + current_pos.imag * 1j
            if not absolute:
                pos += current_pos.real
            segments.append(path.Line(scaler(current_pos), scaler(pos)))
            current_pos = pos

        elif command == 'V':
            y = elements.pop()
            pos = current_pos.real + float(y) * 1j
            if not absolute:
                pos += current_pos.imag * 1j
            segments.append(path.Line(scaler(current_pos), scaler(pos)))
            current_pos = pos

        elif command == 'C':
            control1 = float(elements.pop()) + float(elements.pop()) * 1j
            control2 = float(elements.pop()) + float(elements.pop()) * 1j
            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                control1 += current_pos
                control2 += current_pos
                end += current_pos

            segments.append(path.CubicBezier(scaler(current_pos), scaler(control1), scaler(control2), scaler(end)))
            current_pos = end

        elif command == 'S':
            # Smooth curve. First control point is the "reflection" of
            # the second control point in the previous path.

            if last_command not in 'CS':
                # If there is no previous command or if the previous command
                # was not an C, c, S or s, assume the first control point is
                # coincident with the current point.
                control1 = scaler(current_pos)
            else:
                # The first control point is assumed to be the reflection of
                # the second control point on the previous command relative
                # to the current point.
                control1 = 2 * scaler(current_pos) - segments[-1].control2

            control2 = float(elements.pop()) + float(elements.pop()) * 1j
            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                control2 += current_pos
                end += current_pos

            segments.append(path.CubicBezier(scaler(current_pos), control1, scaler(control2), scaler(end)))
            current_pos = end

        elif command == 'Q':
            control = float(elements.pop()) + float(elements.pop()) * 1j
            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                control += current_pos
                end += current_pos

            segments.append(path.QuadraticBezier(scaler(current_pos), scaler(control), scaler(end)))
            current_pos = end

        elif command == 'T':
            # Smooth curve. Control point is the "reflection" of
            # the second control point in the previous path.

            if last_command not in 'QT':
                # If there is no previous command or if the previous command
                # was not an Q, q, T or t, assume the first control point is
                # coincident with the current point.
                control = scaler(current_pos)
            else:
                # The control point is assumed to be the reflection of
                # the control point on the previous command relative
                # to the current point.
                control = 2 * scaler(current_pos) - segments[-1].control

            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                end += current_pos

            segments.append(path.QuadraticBezier(scaler(current_pos), control, scaler(end)))
            current_pos = end

        elif command == 'A':
            radius = float(elements.pop()) + float(elements.pop()) * 1j
            rotation = float(elements.pop())
            arc = float(elements.pop())
            sweep = float(elements.pop())
            end = float(elements.pop()) + float(elements.pop()) * 1j
           
            if not absolute:
                end += current_pos

            segments.append(path.Arc(current_pos, radius, rotation, arc, sweep, end, scaler))
            current_pos = end

    return segments

def path_from_ellipse(x, y, rx, ry, matrix, state):
    arc = "M %.9f %.9f " % (x-rx,y)
    arc += "A %.9f %.9f 0 0 1 %.9f %.9f " % (rx, ry, x+rx,y) 
    arc += "A %.9f %.9f 0 0 1 %.9f %.9f" % (rx, ry, x-rx,y) 
    return parse_path(arc, matrix=matrix, svgState=state)

def path_from_rect(x,y,w,h,rx,ry, matrix,state):
    if not rx and not ry:
        rect = "M %.9f %.9f h %.9f v %.9f h %.9f Z" % (x,y,w,h,-w)
    else:
        if rx is None:
            rx = ry
        elif ry is None:
            ry = rx
        rect = "M %.9f %.9f h %.9f " % (x+rx,y,w-2*rx)
        rect += "a %.9f %.9f 0 0 1 %.9f %.9f " % (rx, ry, rx, ry)
        rect += "v %.9f " % (h-2*ry)
        rect += "a %.9f %.9f 0 0 1 %.9f %.9f " % (rx, ry, -rx, ry)
        rect += "h %.9f " % -(w-2*rx)
        rect += "a %.9f %.9f 0 0 1 %.9f %.9f " % (rx, ry, -rx, -ry)
        rect += "v %.9f " % -(h-2*ry)
        rect += "a %.9f %.9f 0 0 1 %.9f %.9f Z" % (rx, ry, rx, -ry)
    return parse_path(rect, matrix=matrix, svgState=state)
    
def sizeFromString(text):
    """
    Returns size in mm, if possible.
    """
    text = re.sub(r'\s',r'', text)
    try:
        return float(text)*25.4/96 # px
    except:
        if text[-1] == '%':
            return float(text[:-1]) # NOT mm
        units = text[-2:].lower()
        x = float(text[:-2])
        convert = { 'mm':1, 'cm':10, 'in':25.4, 'px':25.4/96, 'pt':25.4/72, 'pc':12*25.4/72 }
        try:
            return x * convert[units]
        except:
            return x # NOT mm
        
def getPathsFromSVG(svg):
    def updateStateCommand(state,cmd,arg):
        if cmd == 'fill':
            state.fill = rgbFromColor(arg)
        elif cmd == 'fill-opacity':
            state.fillOpacity = float(arg)
        elif cmd == 'fill-rule':
            state.fillRule = arg
#            if state.fill is None:
#                state.fill = (0.,0.,0.)
        elif cmd == 'stroke':
            state.stroke = rgbFromColor(arg)
        elif cmd == 'stroke-opacity':
            state.strokeOpacity = rgbFromColor(arg)
        elif cmd == 'stroke-width':
            state.strokeWidth = float(arg)
        elif cmd == 'vector-effect':
            state.strokeWidthScaling = 'non-scaling-stroke' not in cmd
            # todo better scaling for non-uniform cases?
    
    def updateState(tree,state,matrix):
        state = state.clone()
        try:
            style = re.sub(r'\s',r'', tree.attrib['style']).lower()
            for item in style.split(';'):
                cmd,arg = item.split(':')[:2]
                updateStateCommand(state,cmd,arg)
        except:
            pass
            
        for item in tree.attrib:
            try:
                updateStateCommand(state,item,tree.attrib[item])
            except:
                pass
                
        if state.strokeWidth and state.strokeWidthScaling:
            # this won't work great for non-uniform scaling
            h = abs(applyMatrix(matrix, complex(0,state.strokeWidth)) - applyMatrix(matrix, 0j))
            w = abs(applyMatrix(matrix, complex(state.strokeWidth,0)) - applyMatrix(matrix, 0j))
            state.strokeWidth = (h+w)/2
        return state
        
    def reorder(a,b,c,d,e,f):
        return [a,c,e, b,d,f]            
        
    def updateMatrix(tree, matrix):
        try:
            transformList = re.split(r'\)[\s,]+', tree.attrib['transform'].strip().lower())
        except KeyError:
            return matrix
            
        for transform in transformList:
            cmd = re.split(r'[,()\s]+', transform)
            
            updateMatrix = None
            
            if cmd[0] == 'matrix':
                updateMatrix = reorder(*list(map(float, cmd[1:7])))
            elif cmd[0] == 'translate':
                x = float(cmd[1])
                if len(cmd) >= 3 and cmd[2] != '':
                    y = float(cmd[2])
                else:
                    y = 0
                updateMatrix = reorder(1,0,0,1,x,y)
            elif cmd[0] == 'scale':
                x = float(cmd[1])
                if len(cmd) >= 3 and cmd[2] != '':
                    y = float(cmd[2])
                else:
                    y = x
                updateMatrix = reorder(x,0,0, y,0,0)
            elif cmd[0] == 'rotate':
                theta = float(cmd[1]) * math.pi / 180.
                c = math.cos(theta)
                s = math.sin(theta)
                updateMatrix = [c, -s, 0,  s, c, 0]
                if len(cmd) >= 4 and cmd[2] != '':
                    x = float(cmd[2])
                    y = float(cmd[3])
                    updateMatrix = matrixMultiply(updateMatrix, [1,0,-x, 0,1,-y])
                    updateMatrix = matrixMultiply([1,0,x, 0,1,y], updateMatrix)
            elif cmd[0] == 'skewX':
                theta = float(cmd[1]) * math.pi / 180.
                updateMatrix = [1, math.tan(theta), 0,  0,1,0]
            elif cmd[0] == 'skewY':
                theta = float(cmd[1]) * math.pi / 180.
                updateMatrix = [1,0,0, math.tan(theta),1,0]
                
            matrix = matrixMultiply(matrix, updateMatrix)
            
        return matrix
        
    def updateStateAndMatrix(tree,state,matrix):
        matrix = updateMatrix(tree,matrix)
        return updateState(tree,state,matrix),matrix
        
    def getPaths(paths, matrix, tree, state, savedElements):
        def getFloat(attribute,default=0.):
            try:
                return float(tree.attrib[attribute].strip())
            except KeyError:
                return default

        tag = re.sub(r'.*}', '', tree.tag).lower()
        try:
            savedElements[tree.attrib['id']] = tree
        except KeyError:
            pass
            
        state, matrix = updateStateAndMatrix(tree, state, matrix)
        if tag == 'path':
            path = parse_path(tree.attrib['d'], matrix=matrix, svgState=state)
            if len(path):
                paths.append(path)
        elif tag == 'circle':
            path = path_from_ellipse(getFloat('cx'), getFloat('cy'), getFloat('r'), getFloat('r'), matrix, state)
            paths.append(path)
        elif tag == 'ellipse':
            path = path_from_ellipse(getFloat('cx'), getFloat('cy'), getFloat('rx'), getFloat('ry'), matrix, state)
            paths.append(path)
        elif tag == 'line':
            x1 = getFloat('x1')
            y1 = getFloat('y1')
            x2 = getFloat('x2')
            y2 = getFloat('y2')
            p = 'M %.9f %.9f L %.9f %.9f' % (x1,y1,x2,y2)
            path = parse_path(p, matrix=matrix, svgState=state)
            paths.append(path)
        elif tag == 'polygon':
            points = re.split(r'[\s,]+', tree.attrib['points'].strip())
            p = ' '.join(['M', points[0], points[1], 'L'] + points[2:] + ['Z'])
            path = parse_path(p, matrix=matrix, svgState=state)
            paths.append(path)
        elif tag == 'polyline':
            points = re.split(r'[\s,]+', tree.attrib['points'].strip())
            p = ' '.join(['M', points[0], points[1], 'L'] + points[2:])
            path = parse_path(p, matrix=matrix, svgState=state)
            paths.append(path)
        elif tag == 'rect':
            x = getFloat('x')
            y = getFloat('y')
            w = getFloat('width')
            h = getFloat('height')
            rx = getFloat('rx',default=None)
            ry = getFloat('ry',default=None)
            path = path_from_rect(x,y,w,h,rx,ry, matrix,state)
            paths.append(path)
        elif tag == 'g' or tag == 'svg':
            for child in tree:
                getPaths(paths, matrix, child, state, savedElements)
        elif tag == 'use':
            try:
                link = None
                for tag in tree.attrib:
                    if tag.strip().lower().endswith("}href"):
                        link = tree.attrib[tag]
                        break
                if link is None or link[0] != '#':
                    raise KeyError
                source = savedElements[link[1:]]
                x = 0
                y = 0
                try:
                    x = float(tree.attrib['x'])
                except:
                    pass
                try:
                    y = float(tree.attrib['y'])
                except:
                    pass
                # TODO: handle width and height? (Inkscape does not)
                matrix = matrixMultiply(matrix, reorder(1,0,0,1,x,y))
                getPaths(paths, matrix, source, state, dict(savedElements))
            except KeyError:
                pass

    def scale(width, height, viewBox, z):
        x = (z.real - viewBox[0]) / (viewBox[2] - viewBox[0]) * width
        y = (viewBox[3]-z.imag) / (viewBox[3] - viewBox[1]) * height
        return complex(x,y)
        
    paths = []

    try:
        width = sizeFromString(svg.attrib['width'].strip())
    except KeyError:
        width = None
    try:
        height = sizeFromString(svg.attrib['height'].strip())
    except KeyError:
        height = None
    
    try:
        viewBox = list(map(float, re.split(r'[\s,]+', svg.attrib['viewBox'].strip())))
    except KeyError:
        if width is None or height is None:
            raise KeyError
        viewBox = [0, 0, width*96/25.4, height*96/25.4]
        
    if width is None:
        width = viewBox[2] * 25.4/96
    
    if height is None:
        height = viewBox[3] * 25.4/96
        
    viewBoxWidth = viewBox[2]
    viewBoxHeight = viewBox[3]
    
    viewBox[2] += viewBox[0]
    viewBox[3] += viewBox[1]
    
    try:
        preserve = svg.attrib['preserveAspectRatio'].strip().lower().split()
        if len(preserve[0]) != 8:
            raise KeyError
        if len(preserve)>=2 and preserve[1] == 'slice':
            if viewBoxWidth/viewBoxHeight > width/height:
                # viewbox is wider than viewport, so scale by height to ensure
                # viewbox covers the viewport
                rescale = height / viewBoxHeight
            else:
                rescale = width / viewBoxWidth
        else:
            if viewBoxWidth/viewBoxHeight > width/height:
                # viewbox is wider than viewport, so scale by width to ensure
                # viewport covers the viewbox
                rescale = width / viewBoxWidth
            else:
                rescale = height / viewBoxHeight
        matrix = [rescale, 0, 0,    
                  0, rescale, 0];

        if preserve[0][0:4] == 'xmin':
            # viewBox[0] to 0
            matrix[2] = -viewBox[0] * rescale
        elif preserve[0][0:4] == 'xmid':
            # viewBox[0] to width/2
            matrix[2] = -viewBox[0] * rescale + width/2
        else: # preserve[0][0:4] == 'xmax':
            # viewBox[0] to width
            matrix[2] = -viewBox[0] * rescale + width
        
        if preserve[0][4:8] == 'ymin':
            # viewBox[1] to 0
            matrix[5] = -viewBox[1] * rescale
        elif preserve[0][4:8] == 'ymid':
            # viewBox[0] to width/2
            matrix[5] = -viewBox[1] * rescale + height/2
        else: # preserve[0][4:8] == 'xmax':
            # viewBox[0] to width
            matrix[5] = -viewBox[1] * rescale + height
    except:
        matrix = [ width/viewBoxWidth, 0, -viewBox[0]* width/viewBoxWidth,  
                   0, -height/viewBoxHeight, viewBox[3]*height/viewBoxHeight ]
        
    getPaths(paths, matrix, svg, path.SVGState(), {})

    return ( paths, applyMatrix(matrix, complex(viewBox[0], viewBox[1])), 
                applyMatrix(matrix, complex(viewBox[2], viewBox[3])) )

def parseSVG(svgTree, tolerance=0.05, shader=None, strokeAll=False, pens=None, extractColor = None):
    data = {}
    for path in getPathsFromSVG(svgTree)[0]:
        lines = []

        stroke = strokeAll or (path.svgState.stroke is not None and (extractColor is None or isSameColor(path.svgState.stroke, extractColor)))
        # stroke = True
        strokePen = getPen(pens, path.svgState.stroke)
        # strokenPen = 1
        if strokePen not in data:
            data[strokePen] = []
        for line in path.linearApproximation(error=tolerance): # 返回一个Path对象，里面是经过直线化和共线合并处理的Line对象
            if stroke:
                data[strokePen].append([(line.start.real,line.start.imag),(line.end.real,line.end.imag)])
            lines.append((line.start, line.end)) # lines又存储成了线段的端点组
        if not data[strokePen]:
            del data[strokePen]

        # 需要svg的path的fill属性不为空，并且指定的提取颜色与填充颜色一致才会执行Shader操作
        if shader is not None and shader.isActive() and path.svgState.fill is not None and (extractColor is None or
                isSameColor(path.svgState.fill, extractColor)):
            pen = getPen(pens, path.svgState.fill)
            if pen not in data:
                data[pen] = []

            grayscale = sum(path.svgState.fill) / 3. # 计算灰度，灰度相当于图片的亮度图
            mode = Shader.MODE_NONZERO if path.svgState.fillRule == 'nonzero' else Shader.MODE_EVEN_ODD
            # mode = 1 # nonzero
            if path.svgState.fillOpacity is not None: # fillOpacity是None
                grayscale = grayscale * path.svgState.fillOpacity + 1. - path.svgState.fillOpacity # TODO: real alpha!
            # avoidOutline 是False
            # lines是直线化处理后线段的端点组列表
            fillLines = shader.shade(lines, grayscale, avoidOutline=(path.svgState.stroke is None or strokePen != pen), mode=mode)
            # fillLines 是填充线
            for line in fillLines:
                data[pen].append([(line[0].real,line[0].imag),(line[1].real,line[1].imag)])
            # 仅保留填充线？原先的轮廓线不管了？
            if not data[pen]:
                del data[pen]

    return data

def getPen(pens, color):
    if pens is None:
        return 1

    if color is None:
        color = (0.,0.,0.)

    bestD2 = 10
    bestPen = 1

    for p in pens:
        c = pens[p].color
        d2 = (c[0]-color[0])**2+(c[1]-color[1])**2+(c[2]-color[2])**2
        if d2 < bestD2:
            bestPen = p
            bestD2 = d2

    return bestPen