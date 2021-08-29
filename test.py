import os
import turtle

turtle.home()
turtle.dot()

for p in [(0, 0), (100, 0), (100, -100), (0, -100)]:
    # for p in [(0, 0),(100,0),(0,-100), (-100, 0)]:
    # t.up()
    turtle.goto(p[0], p[1])
    turtle.dot(10)
turtle.heading()

os.system("pause")