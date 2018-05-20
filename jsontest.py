#!/usr/bin/env python

import json
from pcbblock import PCBBlock
from pcb import PCB
from keyboard.layoutengine import KeyboardLayoutEngine

# Convert millimetres to the units used by EDA (decamil? centiinches?)
def mm2eda(mm):
    return mm*100.0/25.4

kle=KeyboardLayoutEngine()
kle.load_layout_from_file('layouts/ftkl left-hand mash pad.json')
(switches, bbox)=kle.layout_switches()

switch=PCBBlock('blocks/cherry mx smd diode.json')
controller=PCBBlock('blocks/teensy 2.0++.json')

pcb=PCB()
iopads={}
sw_cnt=0
for sw in switches:
    x=switch.clone()
    x.translate(mm2eda(sw['x']), mm2eda(sw['y']))
    rowname='ROW%d' % (sw['row']+1)
    colname='COL%d' % (sw['col']+1)
    x.update_net('ROW', rowname)
    x.update_net('COL', colname)
    pcb.add_component(x)
    if rowname not in iopads:
        pad=iopads[rowname]=controller.allocate_io(r'IO\.(.*)', rowname)
        print("Allocated pad %s for %s" % (pad, rowname))
    if colname not in iopads:
        pad=iopads[colname]=controller.allocate_io(r'IO\.(.*)', colname)
        print("Allocated pad %s for %s" % (pad, colname))
    sw_cnt+=1

tx=(pcb.content['BBox'].xmin+pcb.content['BBox'].xmax)/2
ty=pcb.content['BBox'].ymax+100

for block in ([controller]):
    if isinstance(block, str):
        block=PCBBlock('blocks/'+block+'.json').clone()
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
