import FreeCAD as fc
import Part as pt
import Sketcher as sk
import Draft as dt
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicadUtil import kicadReader as kr

import importlib
importlib.reload(kr)

doc = fc.ActiveDocument

# pcb = kr.kiCadPCB(kr.parseBoard("/home/julius/Projects/openEMS_test/openEMS_test.kicad_pcb"))
pcb = kr.kiCadPCB(kr.parseBoard("/home/julius/Projects/openEMS_test/openEMS_test_2/openEMS_test_2.kicad_pcb"))
nets = pcb.getNetNames()
segs = pcb.getSegmentsByNet()
pads = pcb.getPadsByNet()
poly = pcb.getZonesByNet()

ptname = 0

fusions = []

def partmaker():
    global ptname
    obj = doc.addObject("Part::Feature", "part_" + str(ptname))
    ptname += 1
    return obj

for net in nets:
    netparts = []
    for segment in segs[net]:
        for part in segment.makePart(0, 0.1, partmaker):
            netparts.append(part)
        
    for pad in pads[net]:
        for part in pad.makePart(0, 0.1, partmaker):
            netparts.append(part)

    for po in poly[net]:
        for part in po.makePart(0, 0.1, partmaker):
            netparts.append(part)
    if(len(netparts)):        
        if(len(netparts) > 1):
            fus = doc.addObject("Part::MultiFuse","Net_" + net)
            fus.Shapes = netparts
            fus.Refine = True
            fusions.append([fus, net])
        else:
            fusions.append([netparts[0], net])


doc.recompute()

for f in fusions:
    obj = doc.addObject("Part::Feature", "Solid_" + f[1])
    obj.Shape = pt.Solid(pt.Shell(f[0].Shape.Faces))

doc.recompute()


print("done")