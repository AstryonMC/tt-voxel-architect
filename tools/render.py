"""Validate Minecraft command streams and render exposed voxel faces isometrically."""
import argparse
import hashlib
import re
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from model.architect import DEFAULTS,NAMES,PALETTES,FIXED,stream

VALID=set(FIXED+[n for p in PALETTES for n in p])
def validate(text,dims):
    grid={};count=0
    lines=text.splitlines()
    assert lines and lines[-1]=='DONE', 'missing DONE'
    for line in lines[:-1]:
        if line.startswith('[ASIC]'): continue
        t=line.split();assert t[0] in ('/fill','/setblock'),line
        n=6 if t[0]=='/fill' else 3
        assert len(t)==n+2,line
        assert all(re.fullmatch(r'~(0|[1-9][0-9]*)',s) for s in t[1:-1]),line
        c=[int(s[1:]) for s in t[1:-1]]
        if n==3:c+=c
        assert t[-1] in VALID,t[-1]
        limits=(dims[0],dims[2],dims[1])
        assert all(0<=c[i]<=c[i+3]<limits[i] for i in range(3)),line
        count+=1
        for x in range(c[0],c[3]+1):
            for y in range(c[1],c[4]+1):
                for z in range(c[2],c[5]+1):
                    if t[-1]=='air':grid.pop((x,y,z),None)
                    else:grid[x,y,z]=t[-1]
    return grid,count

def color(block):
    base=block.split('[')[0]
    for key,c in [('water',(56,138,201)),('glass',(133,196,204)),('grass',(100,155,68)),('leaves',(63,124,65)),('dirt',(131,94,66)),('gold',(237,192,67)),('lantern',(248,202,117)),('torch',(240,175,68)),('red_bed',(164,53,53)),('oak_log',(96,75,49)),('spruce',(83,64,47)),('dark_oak',(74,55,42)),('oak',(163,126,78)),('mossy',(115,131,102)),('sandstone',(213,186,131)),('prismarine',(69,131,128)),('deepslate',(66,69,78)),('chest',(149,102,48)),('iron',(115,123,129))]:
        if key in base:return c
    return (145,147,141)

def render(text,dims,path,title):
    grid,count=validate(text,dims)
    grid={(x,y,dims[1]-1-z):b for (x,y,z),b in grid.items()}
    scale=13;sy=scale/2;origin=(480,420)
    def proj(x,y,z):return (origin[0]+(x-z)*scale,origin[1]+(x+z)*sy-y*scale)
    im=Image.new('RGB',(960,900),(22,28,39));d=ImageDraw.Draw(im)
    for (x,y,z),block in sorted(grid.items(),key=lambda item:(item[0][0]+item[0][2],item[0][1])):
        rgb=color(block)
        height=.5 if 'slab[' in block else 1
        faces=[((0,1,0),[(x,y+height,z),(x+1,y+height,z),(x+1,y+height,z+1),(x,y+height,z+1)],1.13),
               ((1,0,0),[(x+1,y,z),(x+1,y,z+1),(x+1,y+height,z+1),(x+1,y+height,z)],.68),
               ((0,0,1),[(x,y,z+1),(x+1,y,z+1),(x+1,y+height,z+1),(x,y+height,z+1)],.85)]
        for delta,vertices,shade in faces:
            if tuple(a+b for a,b in zip((x,y,z),delta)) in grid:continue
            c=tuple(min(255,int(v*shade)) for v in rgb)
            d.polygon([proj(*v) for v in vertices],fill=c,outline=tuple(int(v*.82) for v in c))
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24)
    small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
    d.text((44,35),'VOXEL ARCHITECT / '+title.upper(),font=font,fill=(239,224,190))
    d.text((44,75),f'{dims[0]} × {dims[1]} × {dims[2]}  |  palette 0  |  seed 1  |  {count} box commands',font=small,fill=(153,171,188))
    d.text((44,850),'SKY130  •  66 MHz  •  UART procedural architecture',font=small,fill=(153,171,188))
    im.save(path)
    print(f'{path}: {count} commands, {len(grid)} occupied voxels, SHA256 {hashlib.sha256(text.encode()).hexdigest()[:16]}')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--all',action='store_true');p.add_argument('--input',type=Path);p.add_argument('--dims',nargs=3,type=int);p.add_argument('--output',type=Path);a=p.parse_args()
    if a.all:
        root=Path(__file__).resolve().parents[1]
        for i,name in enumerate(NAMES):render(stream(*DEFAULTS[i],1,i),DEFAULTS[i],root/'docs/img'/f'{name}.png',name)
    else:
        p.error('--input, --dims and --output required') if not all((a.input,a.dims,a.output)) else render(a.input.read_text(),a.dims,a.output,a.input.stem)
