import json
from pcbcomponent import PCBComponent
from pcb import PCB

spacing=75

switch=PCBComponent('switch.json')
teensy=PCBComponent('TEENSYPP2.json')

pcb=PCB()
for row in range(5):
    for col in range(15):
        x=switch.clone()
        x.translate(col*spacing+(row % 2)*spacing*0.5, row*spacing)
        x.set_pad_net('1', 'R%d' % row)
        x.set_pad_net('2', 'C%d' % col)
        pcb.add_component(x)
tx=pcb.content['BBox'].xmin+50
ty=(pcb.content['BBox'].ymin+pcb.content['BBox'].ymax)/2
ctrl=teensy.clone()
#ctrl.translate(tx, ty)
pcb.add_component(ctrl)
pcb.add_board_outline()

print(pcb.json())
