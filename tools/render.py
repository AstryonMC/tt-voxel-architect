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
def validate(text,dims,voxelize=True):
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
        assert (c[3]-c[0]+1)*(c[4]-c[1]+1)*(c[5]-c[2]+1)<=32768,line
        count+=1
        if not voxelize:continue
        for x in range(c[0],c[3]+1):
            for y in range(c[1],c[4]+1):
                for z in range(c[2],c[5]+1):
                    if t[-1]=='air':grid.pop((x,y,z),None)
                    else:grid[x,y,z]=t[-1]
    return grid,count

def color(block):
    base=block.split('[')[0]
    if '_door' in base or '_trapdoor' in base:return (111,73,41)
    for key,c in [('water',(56,138,201)),('glass',(133,196,204)),('grass',(100,155,68)),('leaves',(63,124,65)),('dirt',(131,94,66)),('gold',(237,192,67)),('lantern',(248,202,117)),('torch',(240,175,68)),('red_bed',(164,53,53)),('oak_log',(96,75,49)),('spruce',(83,64,47)),('dark_oak',(74,55,42)),('oak',(163,126,78)),('mossy',(115,131,102)),('sandstone',(213,186,131)),('prismarine',(69,131,128)),('deepslate',(66,69,78)),('chest',(149,102,48)),('iron',(115,123,129))]:
        if key in base:return c
    return (145,147,141)

def render(text,dims,path,title):
    grid,count=validate(text,dims)
    occupied=len(grid)
    fine={}
    for (x,y,z),block in grid.items():
        for dx in range(4):
            for dy in range(4):
                for dz in range(4):
                    if '_slab[' in block and (dy>=2)!=('type=top' in block):continue
                    if '_stairs[' in block and dy>=2:
                        high=('facing=north' in block and dz<2 or 'facing=south' in block and dz>=2 or
                              'facing=east' in block and dx>=2 or 'facing=west' in block and dx<2)
                        if not high:continue
                    if '_bed[' in block and dy>=2:continue
                    if block.startswith('chest[') and (dy==3 or dx==3 or dz==3):continue
                    if ('glass_pane' in block or 'iron_bars' in block) and dx!=1:continue
                    if ('_door[' in block or '_trapdoor[' in block) and dz!=0:continue
                    if 'lantern' in block and block!='sea_lantern':
                        if dx not in (1,2) or dz not in (1,2) or dy==3:continue
                    if block=='torch' and (dx!=1 or dz!=1 or dy==3):continue
                    fine[x*4+dx,y*4+dy,dims[1]*4-1-(z*4+dz)]=block
    grid=fine
    tilt=.07 if title=='isla' else .42
    projected=[(x-z,(x+z)*tilt-y) for x,y,z in grid]
    lo=min((v[0] for v in projected),default=0);hi=max((v[0] for v in projected),default=0)
    low=min((v[1] for v in projected),default=0);high=max((v[1] for v in projected),default=0)
    scale=min(780/(hi-lo+2),620/(high-low+2));sy=scale*tilt
    origin=(480-(hi+lo)*scale/2,465-(high+low)*scale/2)
    def proj(x,y,z):return (origin[0]+(x-z)*scale,origin[1]+(x+z)*sy-y*scale)
    im=Image.new('RGB',(960,900),(22,28,39));d=ImageDraw.Draw(im)
    for (x,y,z),block in sorted(grid.items(),key=lambda item:(item[0][0]+item[0][2],item[0][1])):
        rgb=color(block)
        height=1
        faces=[((0,1,0),[(x,y+height,z),(x+1,y+height,z),(x+1,y+height,z+1),(x,y+height,z+1)],1.13),
               ((1,0,0),[(x+1,y,z),(x+1,y,z+1),(x+1,y+height,z+1),(x+1,y+height,z)],.68),
               ((0,0,1),[(x,y,z+1),(x+1,y,z+1),(x+1,y+height,z+1),(x,y+height,z+1)],.85)]
        for delta,vertices,shade in faces:
            if tuple(a+b for a,b in zip((x,y,z),delta)) in grid:continue
            c=tuple(min(255,int(v*shade)) for v in rgb)
            d.polygon([proj(*v) for v in vertices],fill=c)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24)
    small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
    if not grid:d.text((480,465),'EMPTY SCENE',font=font,fill=(153,171,188),anchor='mm')
    d.text((44,35),'VOXEL ARCHITECT / '+title.upper(),font=font,fill=(239,224,190))
    d.text((44,75),f'{dims[0]} × {dims[1]} × {dims[2]}  |  palette 0  |  seed 1  |  {count} box commands',font=small,fill=(153,171,188))
    d.text((44,850),'SKY130  •  66 MHz  •  UART procedural architecture',font=small,fill=(153,171,188))
    im.save(path)
    print(f'{path}: {count} commands, {occupied} occupied voxels, SHA256 {hashlib.sha256(text.encode()).hexdigest()[:16]}')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--all',action='store_true');p.add_argument('--input',type=Path);p.add_argument('--dims',nargs=3,type=int);p.add_argument('--output',type=Path);a=p.parse_args()
    if a.all:
        root=Path(__file__).resolve().parents[1]
        for i,name in enumerate(NAMES):render(stream(*DEFAULTS[i],1,i),DEFAULTS[i],root/'docs/img'/f'{name}.png',name)
    else:
        p.error('--input, --dims and --output required') if not all((a.input,a.dims,a.output)) else render(a.input.read_text(),a.dims,a.output,a.input.stem)
