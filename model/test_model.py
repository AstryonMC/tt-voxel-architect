import unittest
from model.architect import DEFAULTS,PROGRAMS,stream,tiles
from tools.render import validate

class ModelTests(unittest.TestCase):
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
