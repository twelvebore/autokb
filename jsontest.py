#!/usr/bin/env python

import json
from pcbcomponent import PCBComponent
from pcb import PCB
from keyboard.layoutengine import KeyboardLayoutEngine

# Convert millimetres to the units used by EDA (decamil? centiinches?)
def mm2eda(mm):
    return mm*100.0/25.4

kle=KeyboardLayoutEngine()
kle.load_from_file('iso tkl.json')
(switches, bbox)=kle.layout_switches()

pcb_switch=PCBComponent('switch.json')
pcb_teensy=PCBComponent('TEENSYPP2.json')

pcb=PCB()
for sw in switches:
        x=pcb_switch.clone()
        x.translate(mm2eda(sw['x']), mm2eda(sw['y']))
        x.set_pad_net('1', 'R%d' % sw['row'])
        x.set_pad_net('2', 'C%d' % sw['col'])
#        if(sw['row']==2 and sw['col']==13):
        pcb.add_component(x)
pcb.translate(-pcb.content['BBox'].xmin+50, -pcb.content['BBox'].ymin+50)
tx=pcb.content['BBox'].xmin+50
ty=(pcb.content['BBox'].ymin+pcb.content['BBox'].ymax)/2
#ctrl=teensy.clone()
#ctrl.translate(tx, ty)
#pcb.add_component(ctrl)
pcb.add_board_outline()

print(pcb.json())
