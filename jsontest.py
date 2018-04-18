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

switch=PCBComponent('switch.json')

pcb=PCB()
for sw in switches:
        x=switch.clone()
        x.translate(mm2eda(sw['x']), mm2eda(sw['y']))
        x.set_pad_net('1', 'R%d' % sw['row'])
        x.set_pad_net('2', 'C%d' % sw['col'])
        pcb.add_component(x)
tx=(pcb.content['BBox'].xmin+pcb.content['BBox'].xmax)/2
ty=pcb.content['BBox'].ymax+100

for thing in (['avr', 'led', 'usb']):
    cmpt=PCBComponent('kbctrl.'+thing+'.json').clone()
    cmpt.translate(tx-cmpt.bbox.xmin, ty-cmpt.bbox.ymin)
    pcb.add_component(cmpt, update_bound=False)
    tx+=cmpt.bbox.width()+100

# Add the board outline
pcb.add_board_outline()
pcb.add_copper_flood(1)
pcb.add_copper_flood(2)

pcb.translate(4000-pcb.content['BBox'].xmin, 3000-pcb.content['BBox'].ymin)
with open('pcb_source.json', 'w') as fp:
    fp.write(pcb.json())
    fp.close()
