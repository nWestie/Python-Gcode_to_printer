import math
import re
import pandas as pd

# list of values from gcode
xarray = [0]
yarray = [0]
zarray = [0]
earray = [0]
farray = [7200]

# real time at the values given by the gcode
treal = [0]

# list of values at time interval
xpos = [0]
ypos = [0]
zpos = [0]
evalue = [0]
timeint = [0]  # time intervals


tint = 0.001  # time interval seconds
totalint = 0
xi = 0
yi = 0
zi = 0

# collect data from gcode file
gcodefile = open("3DBenchy.gcode", 'r')
while True:
    myline = gcodefile.readline()
    if ';' in myline:
        pass
    if 'G0' in myline or 'G1' in myline:
        if 'X' in myline:
            search = 'X'
            xindex = myline.rfind(search)
            xvalueindex = xindex + 1
            x = myline[xvalueindex:xvalueindex+7]
            x = float(x)
            xarray.append(x)
            x1 = xarray[-2]
            dx = abs(x-x1)
        if 'X' not in myline:
            x = xarray[-1]
            xarray.append(x)
            dx = 0

        if 'Y' in myline:
            search = 'Y'
            yindex = myline.rfind(search)
            yvalueindex = yindex + 1
            y = myline[yvalueindex:yvalueindex+7]
            y = float(y)
            yarray.append(y)
            y1 = yarray[-2]
            dy = abs(y-y1)
        if 'Y' not in myline:
            y = yarray[-1]
            yarray.append(y)
            dy = 0

        if 'Z' in myline:
            search = 'Z'
            zindex = myline.rfind(search)
            zvalueindex = zindex + 1
            z = myline[zvalueindex:zvalueindex+5]
            z = float(z)
            zarray.append(z)
            z1 = zarray[-2]
            dz = abs(z-z1)

        if 'Z' not in myline:
            z = zarray[-1]
            zarray.append(z)
            dz = 0

        if 'E' in myline:
            search = 'E'
            eindex = myline.rfind(search)
            evalueindex = eindex + 1
            eraw = myline[evalueindex:evalueindex+7]
            space = ' '
            e = eraw.partition(space)[0]
            e = float(e)
            earray.append(e)
        if 'E' not in myline:
            e = earray[-1]
            earray.append(e)

        if 'F' in myline:
            search = 'F'
            findex = myline.rfind(search)
            fvalueindex = findex + 1
            f = myline[fvalueindex:fvalueindex+5]
            f = int(float(f))
            feedrate = f/60
            farray.append(f)
        if 'F' not in myline:
            f = farray[-1]
            feedrate = f/60
            farray.append(f)

        d = math.sqrt(dx*dx + dy*dy)  # xy distance
        txy = d/feedrate  # time needed to travel xy distance
        tz = dz/feedrate  # time to travel z distance
        t = max(txy, tz)  # total
        ti = treal[-1]  # initial time
        tf = ti + t  # final time
        tf = float(tf)
        treal.append(tf)

        rows = math.floor(tf/tint)-math.floor(ti/tint)
        for i in range(rows):
            totalint += tint
            timeint.append(totalint)
            if 1:
                p = (totalint-ti)/t

                xn = xi + dx*p
                xn = "{:.4f}".format(xn)
                xn = float(xn)
                xpos.append(xn)

                yn = yi + dy*p
                yn = "{:.4f}".format(yn)
                yn = float(yn)
                ypos.append(yn)

                zn = z
                zn = "{:.4f}".format(zn)
                zn = float(zn)
                zpos.append(zn)

                ex = e
                ex = "{:.4f}".format(ex)
                ex = float(ex)
                evalue.append(ex)

        xi = x
        yi = y

    if 'M107' in myline:
        gcodefile.close()
        break

dict = {'time': timeint, 'X': xpos, 'Y': ypos, 'Z': zpos, 'Ex': evalue}
df = pd.DataFrame(dict)
df.to_csv('benchyTrajs.csv')
