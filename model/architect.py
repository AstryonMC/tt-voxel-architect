"""Executable architectural microcode specification. Coordinates use eighths + offsets."""
from dataclasses import dataclass

DEFAULTS = [(12,12,8), (30,30,12), (26,26,18), (18,18,10), (22,22,10)]
NAMES = ['casa','spawn','castillo','templo','isla']

@dataclass(frozen=True)
class E:
    k: int = 0
    off: int = 0
    def __add__(self, n): return E(self.k, self.off+n)
    def __sub__(self, n): return self+-n
    def value(self, maximum): return max(0,min(maximum, (maximum*self.k//8)+self.off))

END, MID = E(8), E(4)
def e(v): return v if isinstance(v,E) else E(0,v)

PALETTES = [
 ['stone_bricks','oak_log[axis=y]','dark_oak_planks','stone_brick_slab[type=top]','oak_planks','chiseled_stone_bricks','lantern[hanging=false]','glass_pane'],
 ['cut_sandstone','smooth_sandstone','red_sandstone','sandstone_slab[type=top]','smooth_sandstone','chiseled_sandstone','lantern[hanging=false]','yellow_stained_glass_pane'],
 ['prismarine','prismarine_bricks','dark_prismarine','prismarine_slab[type=top]','prismarine_bricks','chiseled_quartz_block','sea_lantern','cyan_stained_glass_pane'],
 ['deepslate_bricks','spruce_log[axis=y]','spruce_planks','deepslate_tile_slab[type=top]','spruce_planks','chiseled_deepslate','lantern[hanging=false]','gray_stained_glass_pane']]
ROLES = ['wall','frame','roof','trim','floor','accent','light','glass']
FIXED = ['air','cobblestone','water','gold_block','iron_bars','grass_block','dirt','stone','oak_leaves[persistent=true]','chest[facing=north]','crafting_table','furnace[facing=north]','red_bed[part=foot,facing=south]','red_bed[part=head,facing=south]','oak_door[half=lower,facing=north]','oak_door[half=upper,facing=north]','oak_trapdoor[facing=north,half=bottom,open=true]','torch','mossy_stone_bricks','cracked_stone_bricks','sea_lantern']
for facing in ['north','south','east','west']:
    ROLES.append('stair_'+facing)
    for p,wood in zip(PALETTES,['dark_oak','red_sandstone','dark_prismarine','spruce']):
        p.append(wood+'_stairs[facing='+facing+',half=bottom]')
ROLES.append('ridge')
for p,wood in zip(PALETTES,['dark_oak','red_sandstone','dark_prismarine','spruce']): p.append(wood+'_slab[type=bottom]')
ROLES += FIXED

def material(role,palette,rng):
    if role=='texture': return ['mossy_stone_bricks','cracked_stone_bricks','stone_bricks','cobblestone'][rng&3] if palette==0 else PALETTES[palette][0]
    return PALETTES[palette][ROLES.index(role)] if role in ROLES[:13] else role

def programs():
    result=[]
    for arch in range(5):
        p=[]
        def box(x,y,z,X,Y,Z,r): p.append((tuple(map(e,(x,y,z,X,Y,Z))),r))
        def point(x,y,z,r): box(x,y,z,x,y,z,r)
        def ring(x,y,z,X,Y,Z,r):
            box(x,y,z,X,Y,z,r);box(x,y,Z,X,Y,Z,r)
            box(x,y,z,x,Y,Z,r);box(X,y,z,X,Y,Z,r)
        def house(x,X,z,Z,b,h):
            box(x,b,z,X,h,Z,'floor' if arch==0 else 'wall');box(x+1,b+1,z+1,X-1,h-1,Z-1,'air')
            box(x,b,z,X,b,Z,'floor')
            ring(x,h,z,X,h,Z,'frame')
            for xx in [x,X]:
                for zz in [z,Z]: box(xx,b+1,zz,xx,h,zz,'frame')
            for xx in [x+2,X-2]:
                for zz in [z,Z]:
                    box(xx,b+2,zz,xx,b+3,zz,'glass')
                    point(xx,b+1,zz,'trim')
                    point(xx+1,b+2,zz,'oak_trapdoor[facing=north,half=bottom,open=true]')
            for zz in [z+2,Z-2]:
                for xx in [x,X]: box(xx,b+2,zz,xx,b+3,zz,'glass')
            for i in range(4):
                box(x-1,h+i,z-1+i,X+1,h+i,Z+1-i,'roof')
                for xx in [x,X]:
                    box(xx,h+i,z+i,xx,h+i,Z-i,'wall')
                    point(xx,h+i,MID,'frame')
                box(x-1,h+i,z-1+i,X+1,h+i,z-1+i,'stair_north')
                box(x-1,h+i,Z+1-i,X+1,h+i,Z+1-i,'stair_south')
            box(x-1,h+4,MID,X+1,h+4,MID+1,'ridge')
        if arch==0:
            box(0,0,0,END,0,END,'cobblestone')
            house(E(0,1),END-1,E(0,2),END-2,0,E(4))
            for xx in [MID]:
                for zz in [2,END-2]: box(xx,1,zz,xx,MID,zz,'frame')
            for zz in [MID]:
                for xx in [1,END-1]: box(xx,1,zz,xx,MID,zz,'frame')
            point(MID,1,2,'oak_door[half=lower,facing=north]');point(MID,2,2,'oak_door[half=upper,facing=north]')
            point(MID,0,1,'trim');point(MID-1,2,1,'light');point(MID+1,2,1,'light')
            point(2,1,END-3,'red_bed[part=head,facing=south]');point(2,1,END-4,'red_bed[part=foot,facing=south]')
            point(END-2,1,END-3,'chest[facing=north]');point(END-2,1,END-4,'crafting_table');point(2,1,4,'furnace[facing=north]')
            box(END-3,1,END-4,END-3,END,END-4,'texture');point(END-3,END,END-4,'trim')
        elif arch==1:
            for i in range(3): box(i,i,i,END-i,i,END-i,'trim' if i!=1 else 'wall')
            box(3,2,3,END-3,2,END-3,'floor')
            for k in [2,3,5,6]:
                box(E(k),2,3,E(k),2,END-3,'accent');box(3,2,E(k),END-3,2,E(k),'accent')
            box(MID-1,2,0,MID+1,2,END,'wall');box(0,2,MID-1,END,2,MID+1,'wall')
            box(MID-4,3,MID-4,MID+4,3,MID+4,'accent')
            box(MID-3,3,MID-3,MID+3,3,MID+3,'water')
            box(MID-1,3,MID-1,MID+1,E(6),MID+1,'frame')
            box(MID-2,E(6),MID-2,MID+2,E(6),MID+2,'trim');point(MID,E(6)+1,MID,'water');point(MID,END,MID,'gold_block')
            for xx in [E(2),E(6)]:
                for zz in [E(2),E(6)]:
                    box(xx-1,3,zz-1,xx+1,3,zz+1,'accent');box(xx,4,zz,xx,E(6),zz,'frame')
                    box(xx-1,E(6)+1,zz-1,xx+1,E(6)+1,zz+1,'trim');point(xx,E(6)+2,zz,'light')
            for xx in [3,END-3]:
                for zz in [3,END-3]: box(xx,3,zz,xx,5,zz,'frame');point(xx,6,zz,'light')
        elif arch==2:
            box(0,0,0,END,0,END,'cobblestone');box(2,0,2,END-2,0,END-2,'floor')
            ring(1,1,1,END-1,E(3),END-1,'wall');ring(1,E(3),1,END-1,E(3),END-1,'trim')
            ring(2,E(3)-1,2,END-2,E(3)-1,END-2,'floor')
            for k in [2,4,6]:
                for zz in [1,END-1]:box(E(k),1,zz,E(k),E(3)-1,zz,'texture')
                for xx in [1,END-1]:box(xx,1,E(k),xx,E(3)-1,E(k),'texture')
            for k in range(9):
                for zz in [1,END-1]: point(E(k),E(3)+1,zz,'accent')
                for xx in [1,END-1]: point(xx,E(3)+1,E(k),'accent')
            for xx in [E(0,1),END-5]:
                for zz in [E(0,1),END-5]:
                    box(xx,1,zz,xx+4,E(6),zz+4,'wall');box(xx+1,1,zz+1,xx+3,E(6)-1,zz+3,'air')
                    ring(xx,E(6),zz,xx+4,E(6),zz+4,'trim')
                    for dx in [0,2,4]:
                        for dz in [0,4]: point(xx+dx,E(6)+1,zz+dz,'accent')
                    for dz in [2]:
                        for dx in [0,4]: point(xx+dx,E(6)+1,zz+dz,'accent')
                    point(xx+2,E(4),zz,'glass');point(xx,E(4),zz+2,'glass')
                    point(xx+4,E(4),zz+2,'glass');point(xx+2,E(4),zz+4,'glass')
                    ring(xx,E(3),zz,xx+4,E(3),zz+4,'accent')
            box(MID-1,0,0,MID+1,0,MID,'accent')
            box(MID-3,1,0,MID+3,E(4),3,'wall');box(MID-1,1,0,MID+1,3,3,'air');box(MID-1,1,1,MID+1,3,1,'iron_bars')
            box(MID-4,E(4)+1,0,MID+4,E(4)+1,4,'trim')
            house(E(3),E(5),E(4),E(6),1,E(5))
            for xx in [MID-3,MID+3]: point(xx,3,0,'torch')
        elif arch==3:
            for i in range(3): box(i,i,i,END-i,i,END-i,'wall' if i%2 else 'accent')
            box(3,2,3,END-3,2,END-3,'floor')
            for xx in [E(0,4),MID,END-4]:
                for zz in [E(0,4),END-4]:
                    point(xx,3,zz,'accent');box(xx,4,zz,xx,END-4,zz,'frame');point(xx,END-3,zz,'accent')
            box(3,END-3,3,END-3,END-3,END-3,'trim')
            for i in range(3):
                box(3+i,END-2+i,3,END-3-i,END-2+i,END-3,'roof')
                box(3+i,END-2+i,3,3+i,END-2+i,END-3,'stair_west')
                box(END-3-i,END-2+i,3,END-3-i,END-2+i,END-3,'stair_east')
            box(MID-1,3,MID-1,MID+1,3,MID+1,'gold_block');point(MID,4,MID,'gold_block')
            for xx in [5,END-5]: point(xx,3,MID,'sea_lantern')
            for i in range(3): box(MID-1,i,i,MID+1,i,i,'stair_north')
        else:
            box(MID, E(4),MID,MID,END-1,MID,'frame')
            box(MID-2,END-2,MID-1,MID+2,END-1,MID+1,'oak_leaves[persistent=true]')
            box(MID-1,END-2,MID-2,MID+1,END-1,MID+2,'oak_leaves[persistent=true]')
            box(MID-1,END,MID-1,MID+1,END,MID+1,'oak_leaves[persistent=true]')
        result.append(p)
    return result

PROGRAMS = programs()
def lfsr(s): return ((s<<1)&65535) | (((s>>15)^(s>>13)^(s>>12)^(s>>10))&1)

def tiles(bounds):
    x,y,z,X,Y,Z=bounds
    for a in range(x,X+1,32):
        for b in range(y,Y+1,32):
            for c in range(z,Z+1,32):
                yield a,b,c,min(a+31,X),min(b+31,Y),min(c+31,Z)

def raw_commands(mx=12,mz=12,my=8,seed=1,flags=0):
    mx,mz,my = [max(1,min(255,v)) for v in (mx,mz,my)]
    arch=flags&15; arch=arch if arch<5 else 0
    palette=(flags>>4)&3; rng=(seed&65535) or 1
    def line(c,r):
        x,y,z,X,Y,Z=c
        return ('/setblock '+ ' '.join('~'+str(v) for v in (x,y,z)) if (x,y,z)==(X,Y,Z) else '/fill '+' '.join('~'+str(v) for v in c))+' '+material(r,palette,rng)+'\n'
    if min(mx,mz,my)<8:
        yield line((0,0,0,mx-1,0,mz-1),'wall');yield 'DONE\n';return
    if arch==4:
        for x in range(mx):
            for z in range(mz):
                dx=abs(x-(mx-1)//2); dz=abs(z-(mz-1)//2)
                d=dx*8//mx+dz*8//mz
                if d>=4: continue
                rng=lfsr(rng); top=min(my-1,(my-1)*4//8+(rng&1))
                bottom=min(top,d)
                yield line((x,bottom,z,x,top,z),'stone')
                yield line((x,max(bottom,top-1),z,x,top,z),'dirt')
                yield line((x,top,z,x,top,z),'grass_block')
    for coords,r in PROGRAMS[arch]:
        rng=lfsr(rng)
        c=tuple(v.value(m) for v,m in zip(coords,(mx-1,my-1,mz-1)*2))
        if any(c[i]>c[i+3] for i in range(3)): continue
        yield line(c,r)
    yield 'DONE\n'

def commands(*args,**kwargs):
    for line in raw_commands(*args,**kwargs):
        fields=line.split()
        if fields[0]!='/fill':
            yield line
            continue
        for c in tiles(tuple(int(v[1:]) for v in fields[1:7])):
            single=c[:3]==c[3:]
            yield ('/setblock ' if single else '/fill ')+' '.join('~'+str(v) for v in (c[:3] if single else c))+' '+fields[-1]+'\n'

def stream(*args): return ''.join(commands(*args))
