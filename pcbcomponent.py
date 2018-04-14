import re
from collections import deque
import copy
import json

json.encoder.FLOAT_REPR = lambda o: format(o, '.2f')

def _pairwise(iterable):
   a=iter(iterable)
   return zip(a, a)

class PCBException(Exception):
    def __init__(self, value):
        self.value=value

    def __str__(self):
        return repr(self.value)

class PCBBoundingBox:
    def __init__(self, xmin, ymin, width=None, height=None, xmax=None, ymax=None):
        self.xmin=float(xmin)
        if(xmax is not None):
            self.xmax=xmax
        else:
            self.xmax=self.xmin+float(width)
        self.ymin=float(ymin)
        if(ymax is not None):
            self.ymax=ymax
        else:
            self.ymax=self.ymin+float(height)

    def __str__(self):
        return '%d %d %d %d ' % (self.xmin, self.xmax, self.ymin, self.ymax)

    def union(self, other):
        return PCBBoundingBox(xmin=min(self.xmin, other.xmin), xmax=max(self.xmax, other.xmax),
                            ymin=min(self.ymin, other.ymin), ymax=max(self.ymax, other.ymax))

    def translate(self, dx, dy):
        self.xmin+=dx
        self.xmax+=dx
        self.ymin+=dy
        self.ymax+=dy

    def json(self):
        return {'x': self.xmin, 'y':self.ymin, 'width': self.xmax-self.xmin, 'height': self.ymax-self.ymin}

class _PCBShapePoint:
    def __init__(self, x, y):
        self.x=float(x)
        self.y=float(y)

    def __str__(self):
        return str(self.x)+' '+str(self.y)

    def translate(self, dx, dy):
        self.x+=dx
        self.y+=dy

class _PCBShapePointList:
    def __init__(self, pt_str):
        self.points=[]
        for (x, y) in _pairwise(pt_str.split(' ')):
            self.points.append(_PCBShapePoint(x, y))

    def __str__(self):
        return ' '.join([str(pt) for pt in self.points])

    def translate(self, dx, dy):
        for x in self.points:
            x.translate(dx, dy)

class _PCBPathElement:
    def __init__(self, w):
        self.cmd=w.popleft()
        if(self.cmd=='A'):
            self.arcargs=(w.popleft(), w.popleft(), w.popleft(), w.popleft(), w.popleft())
        self.coords=_PCBShapePoint(w.popleft(), w.popleft())

    def __str__(self):
        arcargs=' '.join(self.arcargs) if self.cmd=='A' else ''
        return self.cmd+' '+arcargs+' '+str(self.coords)

    def translate(self, dx, dy):
        self.coords.translate(dx, dy)

class _PCBShapePath:
    def __init__(self, path_str):
        path_str=re.sub(r'([LMA])', r' \1 ', path_str)
        path_str=re.sub(r',', ' ', path_str)
        words=deque(path_str.split())
        self.elements=[]
        while(len(words)>0):
            self.elements.append(_PCBPathElement(words))

    def __str__(self):
        return ' '.join([str(el) for el in self.elements])

    def translate(self, dx, dy):
        for el in self.elements:
            el.translate(dx, dy)

class PCBShape:
    id_cntr=1

    def __init__(self, shape_str):
        (shape_type, dummy)=shape_str.split('~', 1)
        shape_defs={'TRACK': {'attr_list': ['stroke width', 'layer id', 'net', 'points', 'id', 'locked'], 'points': ['points']},
                    'SOLIDREGION': {'attr_list': ['layer id', 'net', 'points', 'type', 'id', 'locked'], 'points': ['points']},
                    'HOLE': {'attr_list': ['x', 'y', 'diameter', 'id', 'locked']},
                    'PAD': {'attr_list': ['shape', 'x', 'y', 'width', 'height', 'layer id', 'net', 'number', 'hole radius',
                            'points', 'rotation', 'id', 'hole length', 'hole points', 'plated', 'locked'], 'points': ['points', 'hole points']},
                    'LIB': {'attr_list': ['x', 'y', 'custom attributes', 'rotation', 'import flag', 'id', 'locked']},
                    'COPPERAREA': {'attr_list': ['stroke width', 'layer id', 'net', 'points', 'clearance width', 'fill style',
                            'id', 'thermal', 'keep island', 'copper zone', 'locked'], 'points': ['points']},
                    'RECT': {'attr_list': ['x', 'y', 'width', 'height', 'layer id', 'id', 'locked']},
                    'CIRCLE': {'attr_list': ['x', 'y', 'r', 'stroke width', 'layer id', 'id', 'locked']},
                    'ARC': {'attr_list': ['stroke width', 'layer id', 'net', 'path', 'helper dots', 'id', 'locked'], 'paths': ['path'], 'points': ['helper dots']},
                    'VIA': {'attr_list': ['x', 'y', 'diameter', 'net', 'hole radius', 'id', 'locked']},
                    'DIMENSION': {'attr_list': ['layer id', 'path', 'id', 'locked'], 'paths': ['path']},
                    'TEXT': {'attr_list': ['type', 'x', 'y', 'stroke width', 'rotation', 'mirror', 'layer id', 'net', 'font size',
                            'string', 'text path', 'display', 'id', 'locked'], 'paths': ['text path']}
                    }
        defs=shape_defs[shape_type]
        self.attr_list=['command']+defs['attr_list']
        self.attr=dict(zip(self.attr_list, shape_str.split('~')))
        self.type=self.attr['command']
        if 'points' in defs:
            for key in defs['points']:
                self.attr[key]=_PCBShapePointList(self.attr[key])
        if 'paths' in defs:
            for key in defs['paths']:
                self.attr[key]=_PCBShapePath(self.attr[key])
        for k in ['x', 'y']:
            if k in self.attr: self.attr[k]=float(self.attr[k])
        if 'net' in self.attr: self.attr['net']=''
        if 'id' in self.attr:
            self.attr['id']='shp'+str(PCBShape.id_cntr)
            PCBShape.id_cntr+=1

    def __str__(self):
        return '~'.join([str(self.attr[x]) for x in self.attr_list])

    def translate(self, dx, dy):
        for (key, value) in self.attr.items():
            if(key=='x'): self.attr[key]+=float(dx)
            if(key=='y'): self.attr[key]+=float(dy)
            if(isinstance(value, (_PCBShapePath, _PCBShapePointList))):
                value.translate(dx, dy)

class PCBComponent(json.JSONEncoder):
    id_cntr=1

    def __init__(self, filename):
        with open(filename) as file:
            self.source=json.load(file)
        self.shapes=[PCBShape(x) for x in self.source['shape']]
        bb=self.source['BBox']
        self.bbox=PCBBoundingBox(bb['x'], bb['y'], width=bb['width'], height=bb['height'])
        self.locked=1
        self.pads=dict((sh.attr['number'], sh) for sh in self.shapes if sh.type=='PAD')
        self.id='gge'+str(PCBComponent.id_cntr)
        PCBComponent.id_cntr+=1
#        cx=self.bbox.xmin
#        cy=self.bbox.ymin
#        self.translate(-cx, -cy)

    def __str__(self):
        shape_str='#@$'.join([str(sh) for sh in self.shapes])
        return "LIB~%d~%d~%s~%d~~%s~%d~%s~%d#@$" % (self.bbox.xmin, self.bbox.ymin, "", 0, self.id, self.locked,
                 self.source['head']['uuid'], self.source['head']['utime'])+shape_str

    def translate(self, dx, dy):
        for shape in self.shapes:
            shape.translate(dx, dy)
        self.bbox.translate(dx, dy)
        return self

    def clone(self):
        c=copy.deepcopy(self)
        for sh in c.shapes:
            if 'id' in sh.attr:
               sh.attr['id']='shp'+str(PCBShape.id_cntr)
            PCBShape.id_cntr+=1
        c.id='lib'+str(PCBComponent.id_cntr)
        PCBComponent.id_cntr+=1
        return c

    def json(self):
        return json.dumps(self.shapes, cls=PCBJSONEncoder)

    def set_pad_net(self, pad, net):
        pad=str(pad)
        if(pad not in self.pads):
            raise PCBException("Pad "+pad+" not found")
        self.pads[pad].attr['net']=net

class PCBJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if(isinstance(o, (PCBBoundingBox))):
            return o.json()
        if(isinstance(o, (PCBComponent, PCBShape))):
            return str(o)
        return super().default(o)
