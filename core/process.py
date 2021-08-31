# -*- coding: utf-8 -*-
# @Time    : 2021/8/25 17:58
# @Author  : ShaoJK
# @File    : process.py
# @Remark  :


def removePenBob(data):
    """
    Merge segments with same beginning and end
    为了连笔
    """

    outData = {}

    outSegments = []
    outSegment = []

    for segment in data:
        if not outSegment:
            outSegment = list(segment)
        elif outSegment[-1] == segment[0]:
            outSegment += segment[1:]
        else:
            outSegments.append(outSegment)
            outSegment = list(segment)

    if outSegment:
        outSegments.append(outSegment)

    return outSegments

def dedup(data):
    curPoint = None

    def d2(a,b):
        return (a[0]-b[0])**2+(a[1]-b[1])**2

    newData = {}

    for pen in data:
        newSegments = []
        newSegment = []
        draws = set()

        for segment in data[pen]:
            newSegment = [segment[0]]
            for i in range(1,len(segment)):
                draw = (segment[i-1], segment[i])
                if draw in draws or (segment[i], segment[i-1]) in draws:
                    if len(newSegment)>1:
                        newSegments.append(newSegment)
                    newSegment = [segment[i]]
                else:
                    draws.add(draw)
                    newSegment.append(segment[i])
            if newSegment:
                newSegments.append(newSegment)

        if newSegments:
            newData[pen] = newSegments

    return removePenBob(newData)

def removeCollinear(points, error, pointsToKeep=set()):
    out = []

    lengths = [0]

    for i in range(1, len(points)):  # 获取所有两点之间的长度
        lengths.append(lengths[-1] + abs(points[i] - points[i - 1]))

    def length(a, b):
        return lengths[b] - lengths[a]

    i = 0

    while i < len(points):
        j = len(points) - 1
        while i < j:
            deviationSquared = (length(i, j) / 2) ** 2 - (abs(points[j] - points[i]) / 2) ** 2
            if deviationSquared <= error ** 2 and set(range(i + 1, j)).isdisjoint(pointsToKeep):
                out.append(points[i])
                i = j
                break
            j -= 1
        out.append(points[j])
        i += 1

    return out