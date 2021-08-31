# -*- coding: utf-8 -*-
# @Time    : 2021/8/29 17:03
# @Author  : ShaoJK
# @File    : simulation.py
# @Remark  :

import os
import time
import turtle as t

from core.path import Point


def simulate_point(path):
    with open(path,'r', encoding='UTF-8') as f:
        data = f.read()
    hatchlinesBatchly = []
    for nodes in data.split("\n\n"):
        hatchlines = []
        for hatchline in nodes.split("\n"):
            if hatchline:
                hatchlines.append(tuple([float(point) for point in hatchline.split(",")]))
        hatchlinesBatchly.append(hatchlines)
    draw(hatchlinesBatchly)

def simulate_path():
    pass
def simulate_gcode():
    simulate_path()
    pass

def draw(data):
    t.reset()
    t.color("black")
    # 绘制坐标轴
    t.speed(0)
    axisLength = 600
    t.up()
    t.goto(-axisLength / 2, 0)
    t.down()
    t.goto(axisLength / 2, 0)
    t.up()
    t.goto(0, -axisLength / 2)
    t.down()
    t.goto(0, axisLength / 2)

    t.color("pink")
    t.speed(10)
    for hatchlines in data:
        for line in hatchlines:
            t.up()
            t.goto(line[0], line[1])
            t.down()
            t.goto(line[2], line[3])
    os.system("pause")

if __name__ == '__main__':
    start_time = time.time()
    simulate_point('output.csv')
    print(time.time()-start_time)
