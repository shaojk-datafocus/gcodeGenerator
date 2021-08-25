# -*- coding: utf-8 -*-
# @Time    : 2021/8/25 17:58
# @Author  : ShaoJK
# @File    : process.py
# @Remark  :


def removePenBob(data):
    """
    Merge segments with same beginning and end
    """

    outData = {}

    for pen in data:
        outSegments = []
        outSegment = []

        for segment in data[pen]:
            if not outSegment:
                outSegment = list(segment)
            elif outSegment[-1] == segment[0]:
                outSegment += segment[1:]
            else:
                outSegments.append(outSegment)
                outSegment = list(segment)

        if outSegment:
            outSegments.append(outSegment)

        if outSegments:
            outData[pen] = outSegments

    return outData


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
