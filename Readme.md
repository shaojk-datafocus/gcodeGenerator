
### 路径填充思路

1. 获取到所有路径多边形的各个顶点坐标
2. 使用旋转变换，将坐标映射到填充角度
3. for Y轴最低点到最高点遍历（需要间隔一小段距离）:
    每隔fill_space
    for 遍历所有多边形线段:
        y已知，计算出x，得到交点坐标
   最终得到每条hatchline与多边形交点数组
4. 对每个hatchline的交点数组排序、去重并合并，则得到每两个为一组的hatchline
5. 将所有hatchline交点数组的第i个线段分别合并，再根据起始点进行排序
6. for 遍历每组hatchlines:
      if 如果当前hatchline的开头（末尾）与上一个hatch的开头（末尾）不可以连笔
          对当前的hatchlines进行截断，分成两个数组，然后继续遍历后面的线段
   最终获取到的hatchlines里，每个hatchline都可以练笔操作
   每组hatchline之间不可以连笔，需要台笔换行
7. 将图形的原多边形路径和hatchline分别输出Gcode
