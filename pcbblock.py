import re
from collections import deque
import copy
import json
import re

json.encoder.FLOAT_REPR = lambda o: format(o, '.2f')

class PCBID:
    id_cntr=0

    @staticmethod
    def next_id():
        PCBID.id_cntr+=1
        id='gge'+str(PCBID.id_cntr)
        return id


def fmt(v):
    return format(v, '.2f')

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
        return '%2f %2f %2f %2f ' % (self.xmin, self.xmax, self.ymin, self.ymax)

    def union(self, other):
        return PCBBoundingBox(xmin=min(self.xmin, other.xmin), xmax=max(self.xmax, other.xmax),
                            ymin=min(self.ymin, other.ymin), ymax=max(self.ymax, other.ymax))

    def translate(self, dx, dy):
        self.xmin+=dx
        self.xmax+=dx
        self.ymin+=dy
        self.ymax+=dy

    def width(self):
        return self.xmax-self.xmin

    def height(self):
        return self.ymax-self.ymin

    def json(self):
        return {'x': fmt(self.xmin), 'y': fmt(self.ymin), 'width': fmt(self.xmax-self.xmin), 'height': fmt(self.ymax-self.ymin)}

class _PCBShapePoint:
    def __init__(self, x, y):
        self.x=float(x)
        self.y=float(y)

    def __str__(self):
        return fmt(self.x)+' '+fmt(self.y)

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
        arcargs=' '.join([fmt(x) if isinstance(x, float) else str(x) for x in self.arcargs]) if self.cmd=='A' else ''
        return self.cmd+arcargs+' '+str(self.coords)

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
    def __init__(self, shape_str):
        (shape_type, dummy)=shape_str.split('~', 1)
        shape_defs={'TRACK': {'attr_list': ['stroke width', 'layer id', 'net', 'points', 'id', 'locked'], 'points': ['points']},
                    'SOLIDREGION': {'attr_list': ['layer id', 'net', 'points', 'type', 'id', 'locked'], 'points': ['points']},
                    'HOLE': {'attr_list': ['x', 'y', 'diameter', 'id', 'locked']},
                    'PAD': {'attr_list': ['shape', 'x', 'y', 'width', 'height', 'layer id', 'net', 'number', 'hole radius',
                            'points', 'rotation', 'id', 'hole length', 'hole points', 'plated', 'locked'], 'points': ['points', 'hole points']},
                    'LIB': {'attr_list': ['x', 'y', 'custom attributes', 'rotation', 'import flag', 'id', 'locked', 'uuid', 'utime', 'something']},
                    'COPPERAREA': {'attr_list': ['stroke width', 'layer id', 'net', 'points', 'clearance width', 'fill style',
                            'id', 'thermal', 'keep island', 'copper zone', 'locked'], 'points': ['points']},
                    'RECT': {'attr_list': ['x', 'y', 'width', 'height', 'layer id', 'id', 'locked']},
                    'CIRCLE': {'attr_list': ['x', 'y', 'r', 'stroke width', 'layer id', 'id', 'locked']},
                    'ARC': {'attr_list': ['stroke width', 'layer id', 'net', 'path', 'helper dots', 'id', 'locked'], 'paths': ['path'], 'points': ['helper dots']},
                    'VIA': {'attr_list': ['x', 'y', 'diameter', 'net', 'hole radius', 'id', 'locked']},
                    'DIMENSION': {'attr_list': ['layer id', 'path', 'id', 'locked'], 'paths': ['path']},
                    'TEXT': {'attr_list': ['type', 'x', 'y', 'stroke width', 'rotation', 'mirror', 'layer id', 'net', 'font size',
                            'string', 'text path', 'display', 'id', 'something', 'locked'], 'paths': ['text path']}
                    }
        defs=shape_defs[shape_type]
        self.attr_list=['command']+defs['attr_list']
        self.attr=dict(zip(self.attr_list, shape_str.split('~', maxsplit=len(self.attr_list)-1)))
        self.type=self.attr['command']
        if 'points' in defs:
            for key in defs['points']:
                self.attr[key]=_PCBShapePointList(self.attr[key])
        if 'paths' in defs:
            for key in defs['paths']:
                self.attr[key]=_PCBShapePath(self.attr[key])
        for k in ['x', 'y']:
            if k in self.attr: self.attr[k]=float(self.attr[k])
        if 'locked' in self.attr and self.attr['locked']=='':
            self.attr['locked']=0
        if self.type=='TEXT':
            self.attr['text path']=''
        self.shapes=[]
        if self.type=='LIB':
            (self.attr['something'], shape_str)=self.attr['something'].split('#@$', maxsplit=1)
            self.shapes=[PCBShape(sh) for sh in shape_str.split('#@$')]
            self.custom_attr={}
            for (k, v) in _pairwise(self.attr['custom attributes'].split('`')):
                self.custom_attr[k]=v
        self.update_id()

    def __str__(self):
        str_val='~'.join([(fmt(self.attr[x]) if isinstance(self.attr[x], float) else str(self.attr[x])) for x in self.attr_list])
        if(self.type=='LIB'):
            str_val+='#@$'+'#@$'.join([str(sh) for sh in self.shapes])
        return str_val

    def translate(self, dx, dy):
        for (key, value) in self.attr.items():
            if(key=='x'): self.attr[key]+=float(dx)
            if(key=='y'): self.attr[key]+=float(dy)
            if(isinstance(value, (_PCBShapePath, _PCBShapePointList))):
                value.translate(dx, dy)
        for sh in self.shapes:
            sh.translate(dx, dy)

    def update_id(self):
        if 'id' in self.attr:
            self.attr['id']=PCBID.next_id()
        for sh in self.shapes:
            sh.update_id()
            
class PCBBlock(json.JSONEncoder):
    def __init__(self, filename):
        with open(filename) as file:
            self.source=json.load(file)
        self.shapes=[PCBShape(x) for x in self.source['shape']]
        bb=self.source['BBox']
        self.bbox=PCBBoundingBox(bb['x'], bb['y'], width=bb['width'], height=bb['height'])
        self.locked=1
        self.net_pads=PCBBlock._find_nets(self.shapes)
        self.labels=PCBBlock._find_labels(self.shapes)
        self.id=PCBID.next_id()
        head=self.source['head']
        for k in ('uuid', 'utime'):
            if k not in head: head[k]=''

    def __str__(self):
        shape_str='#@$'.join([str(sh) for sh in self.shapes])
        return shape_str
#        return ("LIB~%s~%s~%s~%d~~%s~%d~%s~%s~#@$" % (fmt(self.bbox.xmin), fmt(self.bbox.ymin), "", 0, self.id, self.locked,
#                 str(self.source['head']['uuid']), str(self.source['head']['utime'])))+shape_str

    @staticmethod
    def _find_nets(shape_list, res=None):
        if res is None: res={}
        for sh in shape_list:
            if sh.type=='LIB':
                res=PCBBlock._find_nets(sh.shapes, res)
            elif 'net' in sh.attr:
                net=sh.attr['net']
                if net not in res: res[net]=[]
                res[net].append(sh)
        return res

    @staticmethod
    def _find_labels(shape_list, prefix=None, res=None):
        if res is None: res={}
        for sh in shape_list:
            if sh.type=='LIB':
                res=PCBBlock._find_labels(sh.shapes, res=res, prefix=sh.custom_attr['prefix'] if 'prefix' in sh.custom_attr else None)
            elif sh.type=='TEXT' and sh.attr['string']=='LBL' and prefix is not None:
                if prefix not in res: res[prefix]=[]
                res[prefix].append(sh)
        return res

    def translate(self, dx, dy):
        for shape in self.shapes:
            shape.translate(dx, dy)
        self.bbox.translate(dx, dy)
        return self

    def clone(self):
        c=copy.deepcopy(self)
        for sh in c.shapes:
            sh.update_id()
        c.id=PCBID.next_id()
        return c

    def json(self):
        return json.dumps(self.shapes, cls=PCBJSONEncoder)

    def update_net(self, net_from, net_to):
        if(net_from not in self.net_pads):
            raise PCBException("Pad "+net_from+" not found")
        for sh in self.net_pads[net_from]:
            sh.attr['net']=net_to
        self.net_pads[net_to]=self.net_pads[net_from]
        del self.net_pads[net_from]

    def assign_labels(self, accum):
        for prefix, shape_list in self.labels.items():
            if prefix not in accum: accum[prefix]=1
            for sh in shape_list:
                lbl=prefix+str(accum[prefix])
                sh.attr['string']=lbl
                sh.attr['display']='Y'
                sh.attr['type']='L'
                accum[prefix]+=1
        return accum

    def allocate_io(self, pattern, net_to):
        pads=list(filter(lambda x: re.match(pattern, x), self.net_pads.keys()))
        net_from=pads[0]
        self.update_net(net_from, net_to)
        return net_from

class PCBJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if(isinstance(o, (PCBBoundingBox, PCBBlock))):
            return o.json()
        if(isinstance(o, (PCBShape))):
            return str(o)
        return super().default(o)
