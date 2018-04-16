import json

class KeyboardLayoutEngine:
    def __init__(self):
        self.layout=[]
        self.properties={}
        self.pitch=19.05

    def load_from_file(self, filename):
        with open(filename) as fp:
            self.raw_data=json.load(fp)

        # Weed out the key layout data from the other properties
        for line in self.raw_data:
            if isinstance(line, dict):
                self.properties.update(line)
            else:
                self.layout.append(line)
        
    def layout_switches(self):
        centre_y=0.0
        switches=[]
        xmin=xmax=ymin=ymax=0.0
        for row, row_data in enumerate(self.layout):
            centre_x=0.0
            next_height = next_width = 1.0
            next_x_offset = next_y_offset = 0.0
            for col, key in enumerate(row_data):
                width=next_width
                height=next_height
                if col==0 and row>0:
                    centre_y+=1.0
                if isinstance(key, dict):
                    if 'x' in key:
                        centre_x+=key['x']
                    if 'y' in key:
                        centre_y+=key['y']
                    if 'w' in key:
                        next_width=key['w']
                    if 'h' in key:
                        next_height=key['h']
                    if 'x2' in key:
                        next_x_offset=key['x2']
                    if 'y2' in key:
                        next_y_offset=key['y2']
                else:
                    x=(centre_x + (width-1)/2 + next_x_offset)*self.pitch
                    y=(centre_y + (height-1)/2 + next_y_offset)*self.pitch
                    sw={'label': key, 'x': x, 'y': y, 'row': row, 'col': col, 'rot': 0.0}
                    switches.append(sw)
                    centre_x+=width
                    next_width=1.0
                    next_height=1.0
                    next_x_offset=0.0
                    next_y_offset=0.0
                    xmin=min(xmin, x-width/2)
                    ymin=min(ymin, y-height/2)
                    xmax=max(xmax, x+width/2)
                    ymax=max(ymax,y+height/2)
        return switches, (xmin*self.pitch, xmax*self.pitch, ymin*self.pitch, ymax*self.pitch)
