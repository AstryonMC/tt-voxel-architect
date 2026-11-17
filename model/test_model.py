import unittest
from model.architect import DEFAULTS,PROGRAMS,stream,tiles
from tools.render import validate

class ModelTests(unittest.TestCase):
    def test_narrow_house_door(self):
        for width in range(8,13):
            for palette in range(4):
                grid,_=validate(stream(width,12,8,1,palette<<4),(width,12,8))
                x=(width-1)//2
                self.assertEqual(grid[x,1,3],'oak_door[half=lower,facing=north]')
                self.assertEqual(grid[x,2,3],'oak_door[half=upper,facing=north]')

    def test_quality_geometry(self):
        grid,_=validate(stream(*DEFAULTS[0],1,0),DEFAULTS[0])
        self.assertEqual(grid[2,4,2],'oak_log[axis=y]')
        self.assertIn('oak_door',grid[5,1,3])
        self.assertIn('stairs',grid[1,5,2])
        self.assertEqual(grid[8,7,8],'stone_brick_slab[type=top]')
        grid,count=validate(stream(*DEFAULTS[4],1,4),DEFAULTS[4])
        self.assertLessEqual(count,400)
        self.assertEqual(grid[10,0,10],'stone')
        self.assertEqual(grid[10,6,10],'oak_log[axis=y]')
        self.assertEqual(grid[10,9,10],'oak_leaves[persistent=true]')

    def test_stone_keep(self):
        grid,_=validate(stream(*DEFAULTS[2],1,2),DEFAULTS[2])
        for y in [2,7,11]:
            self.assertEqual(grid[8,y,14],'stone_bricks')
            self.assertEqual(grid[12,y,18],'stone_bricks')
        self.assertEqual(grid[12,6,14],'stone_bricks')
        for y in [4,5,9,10]: self.assertEqual(grid[10,y,10],'glass_pane')
        self.assertEqual(grid[10,3,10],'stone_brick_slab[type=top]')
        self.assertEqual(grid[7,12,14],'chiseled_stone_bricks')
        self.assertIn('oak_door',grid[12,1,10])
        self.assertEqual(grid[12,0,7],'chiseled_stone_bricks')
        self.assertNotIn((12,1,7),grid)
        self.assertIn('stairs',grid[7,13,9])

    def test_island_profile(self):
        for height,layers in [(10,{8:21,9:9}),(14,{11:21,12:9,13:5})]:
            grid,count=validate(stream(22,22,height,1,4),(22,22,height))
            self.assertLessEqual(count,400)
            ground=(height-1)//2
            self.assertEqual(grid[10,ground,10],'grass_block')
            trunk=list(range(ground+1,(height-1)*6//8+2))
            self.assertGreaterEqual(len(trunk),3)
            for y in trunk: self.assertEqual(grid[10,y,10],'oak_log[axis=y]')
            leaves={y:sum(b.startswith('oak_leaves') and pos[1]==y for pos,b in grid.items()) for y in layers}
            self.assertEqual(leaves,layers)
            bottoms={}
            for (x,y,z),b in grid.items():
                if b=='stone': bottoms[x,z]=min(y,bottoms.get((x,z),y))
            self.assertEqual(bottoms[10,10],0)
            self.assertEqual(bottoms[11,10],1)
            self.assertEqual(bottoms[13,10],2)
            self.assertEqual(grid[10,ground-1,10],'dirt')
            self.assertEqual(sum(y==0 for y in bottoms.values()),1)
            tops={pos[1] for pos,b in grid.items() if b=='grass_block'}
            self.assertEqual(tops,{ground-1,ground})

    def test_fill_limit(self):
        for a in range(5):
            validate(stream(255,255,255,1,a),(255,255,255),voxelize=False)
        for bounds in ((0,0,0,31,31,31),(1,2,3,33,34,35),(254,254,254,254,254,254)):
            chunks=list(tiles(bounds))
            self.assertEqual(sum((c[3]-c[0]+1)*(c[4]-c[1]+1)*(c[5]-c[2]+1) for c in chunks),
                             (bounds[3]-bounds[0]+1)*(bounds[4]-bounds[1]+1)*(bounds[5]-bounds[2]+1))
        self.assertEqual(list(tiles((1,0,0,0,0,0))),[])
        with self.assertRaises(AssertionError):
            validate('/fill ~0 ~0 ~0 ~254 ~0 ~254 stone\nDONE\n',(255,255,255),voxelize=False)

    def test_archetypes_palettes(self):
        for a,dims in enumerate(DEFAULTS):
            for p in range(4):
                for seed in (0,1,43210):
                    text=stream(*dims,seed,a+16*p)
                    grid,count=validate(text,dims)
                    self.assertGreater(len(grid),0)
                    self.assertGreater(count,20)
                    self.assertEqual(text,stream(*dims,seed,a+16*p))

    def test_tiny_and_clamp(self):
        for a in range(5):
            for dims in ((1,1,1),(0,999,2),(8,8,8),(9,17,11)):
                validate(stream(*dims,0,a),tuple(max(1,min(255,d)) for d in dims))

    def test_invalid_streams(self):
        for text in ('','/setblock ~01 ~0 ~0 stone\nDONE\n',
                     '/setblock ~9 ~0 ~0 stone\nDONE\n',
                     '/setblock ~0 ~0 ~0 not_a_block\nDONE\n',
                     '/fill ~1 ~0 ~0 ~0 ~0 ~0 stone\nDONE\n'):
            with self.assertRaises(AssertionError):validate(text,(8,8,8))

    def test_expression_encoding(self):
        for program in PROGRAMS:
            for coords,_ in program:
                for value in coords:
                    self.assertTrue(0<=value.k<=8)
                    self.assertTrue(-32<=value.off<=31)

if __name__=='__main__':unittest.main()
