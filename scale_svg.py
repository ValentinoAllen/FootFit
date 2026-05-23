import re

path = "M14.5,2A1.5,1.5 0 0,0 13,3.5A1.5,1.5 0 0,0 14.5,5A1.5,1.5 0 0,0 16,3.5A1.5,1.5 0 0,0 14.5,2M10,4.5A1.5,1.5 0 0,0 8.5,6A1.5,1.5 0 0,0 10,7.5A1.5,1.5 0 0,0 11.5,6A1.5,1.5 0 0,0 10,4.5M6.5,8A1.5,1.5 0 0,0 5,9.5A1.5,1.5 0 0,0 6.5,11A1.5,1.5 0 0,0 8,9.5A1.5,1.5 0 0,0 6.5,8M18.5,6A1.5,1.5 0 0,0 17,7.5A1.5,1.5 0 0,0 18.5,9A1.5,1.5 0 0,0 20,7.5A1.5,1.5 0 0,0 18.5,6M16,11C16,11 17,14 17,16C17,21 12,22 12,22C12,22 7,21 7,16C7,14 8,11 8,11C8,11 6,12 6,14C6,14 5,20 8.5,23C12,26 15.5,23 19,20C22.5,17 19,13 16,11Z"

scale_x = 11.0 # 240 / ~20
scale_y = 13.0 # 360 / ~25
tx = 15.0
ty = 30.0

def repl(m):
    val = float(m.group(0))
    # We don't know if this is X or Y because we are just matching numbers. 
    # Let's do a proper parse.
    pass

import tokenize
from io import BytesIO

tokens = re.findall(r'[a-zA-Z]+|-?\d*\.?\d+', path)
out = []
is_x = True
for t in tokens:
    if re.match(r'[a-zA-Z]', t):
        out.append(t)
        if t.upper() == 'A':
            # A rx ry x-axis-rotation large-arc-flag sweep-flag x y
            # Needs special parsing. Let's just use svg.path library or manual.
            pass
