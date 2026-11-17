import tempfile
import unittest
from pathlib import Path
from PIL import Image
from tools.render import render


class RenderTests(unittest.TestCase):
    def test_empty_scene(self):
        for text in ('/setblock ~0 ~0 ~0 air\nDONE\n','DONE\n'):
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'empty.png'
                render(text,(1,1,1),path,'empty')
                with Image.open(path) as im:
                    self.assertEqual(im.size,(960,900))
                    self.assertTrue(any(low!=high for low,high in im.crop((300,430,660,500)).getextrema()))

    def test_nonempty_scene(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'stone.png'
            render('/setblock ~0 ~0 ~0 stone\nDONE\n',(1,1,1),path,'stone')
            with Image.open(path) as im:self.assertEqual(im.size,(960,900))

    def test_invalid_scene(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'invalid.png'
            with self.assertRaises(AssertionError):
                render('/setblock ~0 ~0 ~0 invalid\nDONE\n',(1,1,1),path,'invalid')
            self.assertFalse(path.exists())
