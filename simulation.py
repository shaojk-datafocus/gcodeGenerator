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
    with open(path,'r') as f:
        nodes = f.read()
    hatchlines = []
    for hatchline in nodes.split("\n"):
        if hatchline:
            hatchlines.append(tuple([float(point) for point in hatchline.split(",")]))
    draw(hatchlines)

def simulate_path():
    pass
def simulate_gcode():
    simulate_path()
    pass

def draw(data):
    t.reset()
    t.color("red")
    t.speed(7)
    # for p in [(35,10),(10,35),(35,60), (60, 35)]:
    for p in [(10,10),(10,100),(100,100),(100,10)]:
        t.up()
        t.goto(p[0], p[1])
        t.down()
        t.dot()
        time.sleep(0.2)

    for line in data:
        t.up()
        t.goto(line[0], line[1])
        t.down()
        t.goto(line[2], line[3])
    os.system("pause")

if __name__ == '__main__':
    simulate_point('output.csv')

