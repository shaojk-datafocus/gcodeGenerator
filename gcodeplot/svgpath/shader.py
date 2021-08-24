import math
from operator import itemgetter

class Shader(object):
    MODE_EVEN_ODD = 0
    MODE_NONZERO = 1

    def __init__(self, unshadedThreshold=1., lightestSpacing=3., darkestSpacing=0.5, angle=45, crossHatch=False):
        self.unshadedThreshold = unshadedThreshold
        self.lightestSpacing = lightestSpacing
        self.darkestSpacing = darkestSpacing
        self.angle = angle
        self.secondaryAngle = angle + 90
        self.crossHatch = False

    def isActive(self):
        return self.unshadedThreshold > 0.000001
        
    def setDrawingDirectionAngle(self, drawingDirectionAngle):
        self.drawingDirectionAngle = drawingDirectionAngle
        
        if drawingDirectionAngle is None:
            return
        if 90 < (self.angle - drawingDirectionAngle) % 360 < 270:
            self.angle = (self.angle + 180) % 360
        if 90 < (self.secondaryAngle - drawingDirectionAngle) % 360 < 270:
            self.secondaryAngle = (self.secondaryAngle + 180) % 360
        
    def shade(self, polygon, grayscale, avoidOutline=True, mode=None):
        if mode is None: # mode = 1
            mode = Shader.MODE_EVEN_ODD
        if grayscale >= self.unshadedThreshold:
            return []
        # self.unshadedThreshold = 1
        intensity = (self.unshadedThreshold-grayscale) / float(self.unshadedThreshold) # [0,1)
        # self.lightestSpacing = 3
        # self.darkestSpacing = 0.5
        spacing = self.lightestSpacing * (1-intensity) + self.darkestSpacing * intensity
        # polygon是lines,是直线化处理后线段的端点组列表
        # self.angle=45, spacing=0.5, avoidOutline=False, mode = 1, alternate = False
        lines = Shader.shadePolygon(polygon, self.angle, spacing, avoidOutline=avoidOutline, mode=mode, alternate=(self.drawingDirectionAngle is None))
        # lines 是返回的填充线
        if self.crossHatch:
            lines += Shader.shadePolygon(polygon, self.angle+90, spacing, avoidOutline=avoidOutline, mode=mode, alternate=(self.drawingDirectionAngle is None))
        return lines
        
    @staticmethod
    def shadePolygon(polygon, angleDegrees, spacing, avoidOutline=True, mode=None, alternate=True):
        # polygon是lines,是直线化处理后线段的端点组列表
        # angleDegrees = 45, spacing = 0.5, avoidOutline = False, mode = 1, alternate = False
        if mode is None:
            mode = Shader.MODE_EVEN_ODD
    
        rotate = complex(math.cos(angleDegrees * math.pi / 180.), math.sin(angleDegrees * math.pi / 180.))
        # rotate = 0.71 + 0.71i (√2/2)
        # 复数相乘 ≈ 顺时针旋转，复数相除 ≈ 逆时针旋转. rotate的模为1则旋转后大小不变。 否则会放大或缩小rotate模的倍数
        polygon = [(line[0] / rotate,line[1] / rotate) for line in polygon] # 所有的点逆时针旋转45度
        spacing = float(spacing)

        toAvoid = list(set(line[0].imag for line in polygon)|set(line[1].imag for line in polygon))
        # toAvoid 所有点的虚数部

        if len(toAvoid) <= 1:
            deltaY = (toAvoid[0]-spacing/2.) % spacing
        else:
            # find largest interval # 找最大间隙
            toAvoid.sort() # 从小到大排序
            largestIndex = 0
            largestLen = 0
            for i in range(len(toAvoid)): # 遍历所有虚部
                l = (toAvoid[i] - toAvoid[i-1]) % spacing # 求余数
                if l > largestLen: # 记录虚部与spaceing的余数的最大值
                    largestIndex = i
                    largestLen = l
            deltaY = (toAvoid[largestIndex-1] + largestLen / 2.) % spacing

        minY = min(min(line[0].imag,line[1].imag) for line in polygon)
        maxY = max(max(line[0].imag,line[1].imag) for line in polygon)
        #获取所有点虚部的最小值和最大值

        # deltaY是为了让填充线在maxY和minY的之间, 不然填充线会靠经于一侧
        y = minY + ( - minY ) % spacing + deltaY
        # 此时y是y轴最低点坐标
        
        if y > minY + spacing:
            y -= spacing
            
        y += 0.01
        
        odd = False

        all = []
        
        while y < maxY: # 开始遍历每一个spaceing间距行，并且遍历每一条线段
            intersections = []
            for line in polygon: # 遍历每一条线段
                start = line[0]
                end = line[1]
                if end.imag == y or start.imag == y: # roundoff generated corner case -- ignore -- TODO
                    """忽略生成角落的情况
                    即：当线段的两端任意一点于填充线重合的时候，因为是浮点数 这个的概率应该几乎没有
                    """
                    break
                if end.imag < y < start.imag or start.imag < y < end.imag: #如果当前填充线y在线段之间
                    if end.real == start.real: # 如果该线段是竖直的, 在当前线段上放一个点，并记录点在线段起始点的上方还是下方
                        intersections.append(( complex(start.real, y), start.imag<y, line)) # ∵tant90° 不存在
                    else: # 如果线段不是竖直的
                        m = (end.imag-start.imag)/(end.real-start.real)
                        # m * (x - z.real) = y - z.imag
                        # so: x = (y - z.imag) / m + z.real
                        # 求线段上的一个点[x, y](y已知)，使点在线段内
                        intersections.append( (complex((y-start.imag)/m + start.real, y), start.imag<y, line) )
        
            intersections.sort(key=lambda datum: datum[0].real) # 将交点？按照X轴从小到大排序
            # intersections 是当前一层填充线与线段的交点
            thisLine = []
            if mode == Shader.MODE_EVEN_ODD:
                for i in range(0,len(intersections)-1,2):
                    thisLine.append((intersections[i], intersections[i+1]))
            elif mode == Shader.MODE_NONZERO:
                count = 0
                for i in range(0,len(intersections)-1): # 遍历所有的交点
                    if intersections[i][1]: # 线段起始点y值低于交点y值
                        count += 1
                    else: # 线段起始点y值高于交点y值
                        count -= 1
                    if count != 0: # TODO： count=0时是线不填充的时候，因为这里的数据是使用一条线画出来的图形。
                        thisLine.append((intersections[i], intersections[i+1])) # 把两个交点连接起来，记录两点数据
            else:
                raise ValueError()
                   
            if odd and alternate: # 不执行
                thisLine = list(reversed([(l[1],l[0]) for l in thisLine]))
                
            if not avoidOutline and len(thisLine) and len(all) and all[-1][1][2] == thisLine[0][0][2]:
                # follow along outline to avoid an extra pen bob
                # 如果all的最后一条线的line和这一行的第一条line是同一个line
                # 没有要求避免轮廓线， all和thisLine不是空集
                all.append((all[-1][1], thisLine[0][0])) # 添加上一个最后一行末尾点到这一行首点的路径。应该类似于是横向扫描回到行起始位置
                
            all += thisLine # 把整行数据保存
                
            odd = not odd
                
            y += spacing

        return [(line[0][0]*rotate, line[1][0]*rotate) for line in all] # 把所有点顺时针旋转回去
    
                    
if __name__ == '__main__':
    polygon=(0+0j, 10+10j, 10+0j, 0+0j)
    print(shadePolygon(polygon,90,1))
                    