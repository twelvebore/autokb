#!/usr/bin/env python

import json
from pcbblock import PCBBlock
from pcb import PCB
from keyboard.layoutengine import KeyboardLayoutEngine

# Convert millimetres to the units used by EDA (decamil? centiinches?)
def mm2eda(mm):
    return mm*100.0/25.4

kle=KeyboardLayoutEngine()
kle.load_layout_from_file('layouts/iso tkl.json')
(switches, bbox)=kle.layout_switches()

switch=PCBBlock('blocks/cherry mx smd diode.json')

pcb=PCB()
for sw in switches:
    x=switch.clone()
    x.translate(mm2eda(sw['x']), mm2eda(sw['y']))
    x.update_net('ROW', 'ROW_%d' % (sw['row']+1))
    x.update_net('COL', 'COL_%d' % (sw['col']+1))
    pcb.add_component(x)
tx=(pcb.content['BBox'].xmin+pcb.content['BBox'].xmax)/2
ty=pcb.content['BBox'].ymax+100

for thing in (['teensy 2.0']):
    block=PCBBlock('blocks/'+thing+'.json').clone()
    block.translate(tx-block.bbox.xmin, ty-block.bbox.ymin)
    pcb.add_component(block, update_bound=False)
    tx+=block.bbox.width()+100

# Add the board outline
pcb.add_board_outline()
pcb.add_copper_flood(1)
pcb.add_copper_flood(2)

pcb.translate(4000-pcb.content['BBox'].xmin, 3000-pcb.content['BBox'].ymin)
with open('pcb_source.json', 'w') as fp:
    fp.write(pcb.json())
    fp.close()

print(pcb.label_accumulator)
