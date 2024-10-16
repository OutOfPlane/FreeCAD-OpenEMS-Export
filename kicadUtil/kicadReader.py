import typing
import FreeCAD as fc
import Part as pt
import Sketcher as sk
import numpy as np

class keyValueSet():
    def __init__(self):
        self._item = None
        self._unset = True
        self._key = ""
        pass

    def set(self, key, item):
        self._key = key
        self._item = item
        self._unset = False

    def get(self):
        return self._item
    
    def getKey(self):
        return self._key
    
    def search(self, key):
        out = []
        if(type(self._item) is list):
            for i in self._item:
                if(type(i) is keyValueSet):
                    if(i._key == key):
                        out.append(i)
        return out
    
    def searchUnique(self, key):
        if(type(self._item) is list):
            for i in self._item:
                if(type(i) is keyValueSet):
                    if(i._key == key):
                        return i._item
        return None

    def isUnset(self):
        return self._unset
    
    def dump(self, lvl = 0) -> str:
        out = ""
        out += "  " * lvl
        out += self._key + " = "
        if(type(self._item) is list):
            out += "\n"
            out += "  " * (lvl + 1) + "[" + "\n"
            for i in self._item:
                if(type(i) is keyValueSet):
                    out += i.dump(lvl + 2)
                else:
                    out += "  " * (lvl + 2) + str(i) + "\n"
            out += "  "*(lvl+1)+"]"
        elif(self._item is not None):
            out += str(self._item)
        else:
            out += "[EMPTY]"
        out += "\n"
        return out

def __parse(file: typing.TextIO) -> keyValueSet:
    parsed = keyValueSet()
    #step 1: parse key
    key = ""
    data = []
    dat = file.read(1)
    while(dat != " " and dat != "\n" and dat != "\r" and dat != "" and dat != ")"):
        key += dat
        dat = file.read(1)
    # print(key)

    while(dat != ")" and dat != ""):
        val = ""
        dat = file.read(1)  
        if(dat == '"'):
            #value is string type
            dat = file.read(1)
            while(dat != '"' and dat != ""):
                val += dat
                dat = file.read(1)
            data.append(val)
            dat = file.read(1)
        elif(dat == "("):
            #value is object type
            prsd = __parse(file)
            data.append(prsd)
        elif(dat != " " and dat != "\n" and dat != "\r" and dat != "" and dat != "\t"):
            #value is other non space containing set of characters
            while(dat != " " and dat != "" and dat != ")" and dat != "\n" and dat != "\r"):
                val += dat
                dat = file.read(1)
            data.append(val)
        if(dat == ")"):
            parsed.set(key, data)
            return parsed
    parsed.set(key, data)
    return parsed



def parseBoard(filename):
    out = keyValueSet()
    with open(filename, 'r') as f:
        dat = f.read(1)
        if(dat != "("):
            print("Invalid board file")
        else:
            out = __parse(f)
    return out

def strToFloatList(inp: list) -> list:
    out = []
    for i in inp:
        out.append(float(i))
    return out

def getNormOrthoVect(dx, dy):
    ox = dy
    oy = -dx
    l = np.sqrt(ox**2 + oy**2)
    return ox/l, oy/l


class geometry(object):
    def __init__(self):
        pass

    def makePart(self, z_coord):
        pass

class line(geometry):
    def fromKeyValueSet(data: keyValueSet) -> "line":
        inpType = data.getKey()
        if(inpType == "segment"):
            startx, starty = strToFloatList(data.searchUnique("start"))
            endx, endy = strToFloatList(data.searchUnique("end"))
            w = data.searchUnique("width")[0]
            return line(startx, starty, endx, endy, w)
        else:
            raise Exception(f"type {inpType} not castable into line Object")

    def __init__(self, x1, y1, x2, y2, width):
        super().__init__()
        self.x1 = float(x1)
        self.x2 = float(x2)
        self.y1 = float(y1)
        self.y2 = float(y2)
        self.width = float(width)

    def moveRealtive(self, dx, dy):
        dx = float(dx)
        dy = float(dy)
        self.x1 += dx
        self.x2 += dx
        self.y1 += dy
        self.y2 += dy



    def makePart(self, z_coord):
        dx = self.x2 - self.x1
        dy = self.y2 - self.y1
        ox, oy = getNormOrthoVect(dx, dy)
        ox *= self.width/2
        oy *= self.width/2

        ux = (dx/np.sqrt(dx**2 + dy**2))*self.width
        uy = (dy/np.sqrt(dx**2 + dy**2))*self.width
        out = []
        out.append(
            pt.makePolygon([
                fc.Vector(self.x1 - ox, self.y1 - oy, z_coord),
                fc.Vector(self.x2 - ox, self.y2 - oy, z_coord),
                fc.Vector(self.x2 + ox, self.y2 + oy, z_coord),
                fc.Vector(self.x1 + ox, self.y1 + oy, z_coord),
                fc.Vector(self.x1 - ox, self.y1 - oy, z_coord),
            ])
        )

        out.append(
            pt.makeCircle(
                self.width/2,
                fc.Vector(self.x1, self.y1, z_coord)
        ))
        out.append(
            pt.makeCircle(
                self.width/2,
                fc.Vector(self.x2, self.y2, z_coord)
        ))
        return out

class rect(geometry):
    def fromKeyValueSet(data: keyValueSet) -> "rect":
        inpType = data.getKey()
        if(inpType == "pad"):
            padType = data.get()[2]
            if(padType == "rect"):
                sizex, sizey = data.searchUnique("size")
                atx, aty, *rot = data.searchUnique("at")
                return rect(atx, aty, sizex, sizey)
            else:
                raise Exception(f"unsupported Pad Type: {padType}")
        else:
            raise Exception(f"type {inpType} not castable into line Object")

    def __init__(self, x, y, w, h):
        super().__init__()
        self.x = float(x)
        self.w = float(w)
        self.y = float(y)
        self.h = float(h)

    def moveRealtive(self, dx, dy):
        dx = float(dx)
        dy = float(dy)
        self.x += dx
        self.y += dy

    def makePart(self, z_coord):
        return [pt.makePolygon([
            fc.Vector(self.x - self.w/2, self.y - self.h/2, z_coord),
            fc.Vector(self.x + self.w/2, self.y - self.h/2, z_coord),
            fc.Vector(self.x + self.w/2, self.y + self.h/2, z_coord),
            fc.Vector(self.x - self.w/2, self.y + self.h/2, z_coord),
            fc.Vector(self.x - self.w/2, self.y - self.h/2, z_coord)
        ])]
        
class circle(geometry):
    def fromKeyValueSet(data: keyValueSet) -> "circle":
        inpType = data.getKey()
        if(inpType == "pad"):
            padType = data.get()[2]
            if(padType == "circle"):
                sizex, sizey = data.searchUnique("size")
                atx, aty, *rot = data.searchUnique("at")
                return circle(atx, aty, sizex)
            else:
                raise Exception(f"unsupported Pad Type: {padType}")
        else:
            raise Exception(f"type {inpType} not castable into line Object")

    def __init__(self, x, y, r):
        super().__init__()
        self.x = float(x)
        self.y = float(y)
        self.r = float(r)

    def moveRealtive(self, dx, dy):
        dx = float(dx)
        dy = float(dy)
        self.x += dx
        self.y += dy

    def makePart(self, z_coord):
        return [pt.makeCircle(self.r, fc.Vector(self.x, self.y, z_coord))]
    

def padFromKeyValueSet(data: keyValueSet) -> geometry:
    inpType = data.getKey()
    if(inpType == "pad"):
        padType = data.get()[2]
        if(padType == "circle"):
            return circle.fromKeyValueSet(data)
        if(padType == "rect"):
            return rect.fromKeyValueSet(data)


class kiCadPCB():
    def __init__(self, boardData: keyValueSet):
        self._data = boardData

    def dump(self):
        print(self._data.dump())

    def _filterListByValue(kvlist, itemidx, item):
        out = []
        for i in kvlist:
            if(type(i) is keyValueSet):
                itms = i.get()
                if(itemidx < len(itms)):
                    if(type(itms[itemidx]) is not keyValueSet):
                        if(itms[itemidx] == item):
                            out.append(i)
        return out

    def getLayers(self):
        return self._data.search("layers")[0].get()
    
    def getSignalLayers(self):
        lrs = self.getLayers()
        sig_lrs = kiCadPCB._filterListByValue(lrs, 1, "signal")
        return sig_lrs
    
    def getSignalLayerNames(self):
        lrs = self.getSignalLayers()
        out = []
        for l in lrs:
            out.append(l.get()[0])
        return out
    
    def getNets(self):
        return self._data.search("net")
    
    def getNetNames(self):
        nets = self.getNets()
        out = []
        for n in nets:
            out.append(n.get()[1])
        return out

    def getFootprints(self):
        return self._data.search("footprint")
    
    def getGridOrigin(self):
        return strToFloatList(self._data.search("setup")[0].searchUnique("grid_origin"))
    
    def getSegmentsByNet(self):
        out = {}
        netLookup = {}
        for n in self.getNets():
            netLookup[n.get()[0]] = n.get()[1]
            out[n.get()[1]] = []

        segs = self._data.search("segment")
        signal_layers = self.getSignalLayerNames()
        orig = self.getGridOrigin()

        for seg in segs:
            seg_layer = seg.searchUnique("layer")[0]
            if(not seg_layer in signal_layers):
                continue
            seg_net = seg.searchUnique("net")[0]
            ln = line.fromKeyValueSet(seg)
            ln.moveRealtive(-orig[0], -orig[1])
            out[netLookup[seg_net]].append(ln)

        return out
    
    def getPadsByNet(self):
        out = {}
        netLookup = {}
        for n in self.getNets():
            netLookup[n.get()[0]] = n.get()[1]
            out[n.get()[1]] = []

        signal_layers = self.getSignalLayerNames()
        orig = self.getGridOrigin()

        footprints = self.getFootprints()
        for fp in footprints:
            pads = fp.search("pad")
            fp_position = fp.searchUnique("at")
            for pad in pads:
                pad_layer = pad.searchUnique("layers")
                signalpad = False
                for l in signal_layers:
                    if(l in pad_layer):
                        signalpad = True
                        break
                if(not signalpad):
                    continue
                pad_net = pad.searchUnique("net")[0]
                pd = padFromKeyValueSet(pad)
                pd.moveRealtive(fp_position[0], fp_position[1])
                pd.moveRealtive(-orig[0], -orig[1])
                out[netLookup[pad_net]].append(pd)

        return out
