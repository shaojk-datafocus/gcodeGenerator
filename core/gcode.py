# -*- coding: utf-8 -*-
# @Time    : 2021/8/26 10:19
# @Author  : ShaoJK
# @File    : gcode.py
# @Remark  :
import cmath
import math
import re
import sys

from core.plot import evaluate, Plotter, SCALE_NONE, Scale, SCALE_DOWN_ONLY, gcodeHeader


def emitGcode(data, pens={}, plotter=Plotter(), scalingMode=SCALE_NONE, align=None, tolerance=0, gcodePause="@pause",
              pauseAtStart=False, simulation=False):
    if len(data) == 0:
        return None
    # data 笔的字典， 值是所有线段的数组，每个线段是两个点数据，每个点数据是XY轴坐标的元组
    # [[(13.0, 283.0), (14.0, 284.0)], ...]
    xyMin = [float("inf"), float("inf")]
    xyMax = [float("-inf"), float("-inf")]

    allFit = True

    scale = Scale()
    # scale的scale控制缩放
    scale.offset = (plotter.xyMin[0], plotter.xyMin[1])  # scale放入plotter的范围 XY均0~300

    for pen in data:  # 遍历每个笔
        for segment in data[pen]:  # 遍历每个线段
            for point in segment:  # 遍历每个点，就两个点
                if not plotter.inRange(scale.scalePoint(point)):  # 判断点是否在plotter的画图范围内
                    allFit = False
                for i in range(2):
                    xyMin[i] = min(xyMin[i], point[i])  # 记录图形的最大最小范围
                    xyMax[i] = max(xyMax[i], point[i])

    if scalingMode == SCALE_NONE:
        if not allFit:
            sys.stderr.write("Drawing out of range: " + str(xyMin) + " " + str(xyMax) + "\n")
            return None
    elif scalingMode != SCALE_DOWN_ONLY or not allFit:
        if xyMin[0] > xyMax[0]:
            return None
        scale = Scale()
        scale.fit(plotter, xyMin, xyMax)

    if align is not None:
        scale.align(plotter, xyMin, xyMax, align)

    if not simulation:
        gcode = gcodeHeader(plotter)
    else:
        gcode = []
        gcode.append('<?xml version="1.0" standalone="yes"?>')
        gcode.append(
            '<svg width="%.4fmm" height="%.4fmm" viewBox="%.4f %.4f %.4f %.4f" xmlns="http://www.w3.org/2000/svg" version="1.1">' % (
                plotter.xyMax[0] - plotter.xyMin[0], plotter.xyMax[1] - plotter.xyMin[0], plotter.xyMin[0],
                plotter.xyMin[1], plotter.xyMax[0], plotter.xyMax[1]))

    def park():
        """停止，抬笔"""
        if not simulation:
            lift = plotter.safeLiftCommand or plotter.liftCommand
            if lift:
                gcode.extend(processCode(lift, plotter))
            else:
                gcode.append('G00 F%.1f Z%.3f; pen park !!Zpark' % (plotter.zSpeed * 60., plotter.safeUpZ))

    park()
    if not simulation:  # 移动到原点
        gcode.append('G00 F%.1f Y%.3f; !!Ybottom' % (plotter.moveSpeed * 60., plotter.xyMin[1]))
        gcode.append('G00 F%.1f X%.3f; !!Xleft' % (plotter.moveSpeed * 60., plotter.xyMin[0]))

    class State(object):
        pass

    state = State()
    state.time = (plotter.xyMin[1] + plotter.xyMin[0]) / plotter.moveSpeed
    state.curXY = plotter.xyMin
    state.curZ = plotter.safeUpZ
    state.penColor = (0., 0., 0.)  # penColor仅在模拟的情况下才会使用，用作svg的fill属性

    def distance(a, b):
        """计算两点的欧几里得距离"""
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def penUp(force=False):
        if state.curZ is None or state.curZ not in (plotter.safeUpZ, plotter.penUpZ) or force:
            if not simulation:
                if plotter.liftCommand:
                    gcode.extend(processCode(plotter.liftCommand, plotter))
                else:
                    gcode.append('G00 F%.1f Z%.3f; pen up !!Zup' % (plotter.zSpeed * 60., plotter.penUpZ))
            if state.curZ is not None:
                state.time += abs(plotter.penUpZ - state.curZ) / plotter.zSpeed
            state.curZ = plotter.penUpZ

    def penDown(force=False):
        if state.curZ is None or state.curZ != plotter.workZ or force:
            if not simulation:
                if plotter.downCommand:
                    gcode.extend(processCode(plotter.downCommand, plotter))
                else:
                    gcode.append('G00 F%.1f Z%.3f; pen down !!Zwork' % (plotter.zSpeed * 60., plotter.workZ))
            state.time += abs(state.curZ - plotter.workZ) / plotter.zSpeed
            state.curZ = plotter.workZ

    def penMove(down, speed, p, force=False):
        def flip(y):
            return plotter.xyMax[1] - (y - plotter.xyMin[1])

        if state.curXY is None:
            d = float("inf")
        else:
            d = distance(state.curXY, p)
        if d > tolerance or force:
            if down:
                penDown(force=force)
            else:
                penUp(force=force)
            if not simulation:
                gcode.append('G0%d F%.1f X%.3f Y%.3f; %s !!Xleft+%.3f Ybottom+%.3f' % (
                    1 if down else 0, speed * 60., p[0], p[1], "draw" if down else "move",
                    p[0] - plotter.xyMin[0], p[1] - plotter.xyMin[1]))
            else:
                start = state.curXY if state.curXY is not None else plotter.xyMin
                color = [int(math.floor(255 * x + 0.5)) for x in (state.penColor if down else (0, 0.5, 0))]
                thickness = 0.15 if down else 0.1
                end = complex(p[0], flip(p[1]))
                gcode.append(
                    '<line x1="%.3f" y1="%.3f" x2="%.3f" y2="%.3f" stroke="rgb(%d,%d,%d)" stroke-width="%.2f"/>'
                    % (start[0], flip(start[1]), end.real, end.imag, color[0], color[1], color[2], thickness))
                ray = end - complex(start[0], flip(start[1]))
                if abs(ray) > 0:
                    ray = ray / abs(ray)
                    for theta in [math.pi * 0.8, -math.pi * 0.8]:
                        head = end + ray * cmath.rect(max(0.3, min(2, d * 0.25)), theta)
                        gcode.append(
                            '<line x1="%.3f" y1="%.3f" x2="%.3f" y2="%.3f" stroke="rgb(0,128,0)" stroke-linejoin="round" stroke-width="0.1"/>'
                            % (end.real, end.imag, head.real, head.imag))

            if state.curXY is not None:
                state.time += d / speed
            state.curXY = p

    for pen in sorted(data):  # 遍历每个笔
        if pen != 1:
            state.curZ = None
            state.curXY = None

        state.penColor = penColor(pens, pen)

        s = scale.clone()

        if pens is not None and pen in pens:
            s.offset = (s.offset[0] - pens[pen].offset[0], s.offset[1] - pens[pen].offset[1])

        newPen = True

        for segment in data[pen]:  # 遍历每个线段
            penMove(False, plotter.moveSpeed, s.scalePoint(segment[0]))

            if newPen and (pen != 1 or pauseAtStart) and not simulation:
                gcode.append(gcodePause + ' load pen: ' + describePen(pens, pen))
                penMove(False, plotter.moveSpeed, s.scalePoint(segment[0]), force=True)
            newPen = False

            for i in range(1, len(segment)):
                penMove(True, plotter.drawSpeed, s.scalePoint(segment[i]))

    park()

    if simulation:
        gcode.append('</svg>')
    else:
        gcode.extend(processCode(plotter.endCode, plotter))
    quiet = False
    if not quiet:
        sys.stderr.write('Estimated printing time: %dm %.1fs\n' % (state.time // 60, state.time % 60))
        sys.stderr.flush()

    return gcode


def processCode(code, plotter):
    if not code:
        return []

    pattern = r'\{\{([^}]+)\}\}'  # 获取{{ }}的标识，

    data = tuple(evaluate(expr, plotter.variables, plotter.formulas) for expr in re.findall(pattern, code))
    # evaluate是将命令中一些规定的语句转换成具体数值

    formatString = re.sub(pattern, '', code.replace('|', '\n'))

    return [formatString % data]


def penColor(pens, pen):
    if pens is not None and pen in pens:
        return pens[pen].color
    else:
        return (0.,0.,0.)


def describePen(pens, pen):
    if pens is not None and pen in pens:
        return pens[pen].description
    else:
        return str(pen)