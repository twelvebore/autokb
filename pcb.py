import json
from pcbcomponent import PCBJSONEncoder, PCBBoundingBox, PCBShape
import copy

class PCB:
    def __init__(self):
        with open('pcb_template.json') as f:
            self.content=json.load(f)
            bb=self.content['BBox']
            self.content['BBox']=PCBBoundingBox(bb['x'], bb['y'], width=bb['width'], height=bb['height'])
            self.content['shape']=[]

    def add_component(self, component):
        if(len(self.content['shape'])==0):
            self.content['BBox']=copy.copy(component.bbox)            
        else:
            self.content['BBox']=self.content['BBox'].union(component.bbox)
        self.content['shape'].append(component)

    def add_board_outline(self, border=20.0):
        bb=self.content['BBox']
        xleft=bb.xmin-border
        xright=bb.xmax+border
        ybottom=bb.ymin-border
        ytop=bb.ymax+border
        shape_str="TRACK~1~10~~%d %d %d %d %d %d %d %d %d %d~outline~1" % (xleft, ytop, xright, ytop, xright, ybottom, xleft, ybottom, xleft, ytop)
        sh=PCBShape(shape_str)
        sh.bbox=PCBBoundingBox(xleft, ybottom, xmax=xright, ymax=ytop)
        self.add_component(sh)

    def json(self):
        return json.dumps(self.content, cls=PCBJSONEncoder, indent=2)