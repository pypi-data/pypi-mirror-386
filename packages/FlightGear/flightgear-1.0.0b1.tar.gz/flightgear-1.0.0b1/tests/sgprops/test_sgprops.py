#! /usr/bin/env python3

import os
import unittest

from flightgear.meta import sgprops


baseDir = os.path.dirname(__file__)

def testData(*args):
    return os.path.join(baseDir, "testData", *args)


class SGProps(unittest.TestCase):

    def test_parse(self):
        parsed = sgprops.readProps(testData("props1.xml"))

        self.assertEqual(parsed.getValue("value"), 42)
        self.assertEqual(type(parsed.getValue("value")), int)

        valNode = parsed.getChild("value")
        self.assertEqual(valNode.parent, parsed)
        self.assertEqual(valNode.name, "value")

        self.assertEqual(valNode.value, 42)
        self.assertEqual(type(valNode.value), int)

        with self.assertRaises(IndexError):
            missingNode = parsed.getChild("missing")

        things = parsed.getChildren("thing")
        self.assertEqual(len(things), 3)

        self.assertEqual(things[0], parsed.getChild("thing", 0));
        self.assertEqual(things[1], parsed.getChild("thing", 1));
        self.assertEqual(things[2], parsed.getChild("thing", 2));

        self.assertEqual(things[0].getValue("value"), "apple");
        self.assertEqual(things[1].getValue("value"), "lemon");
        self.assertEqual(things[2].getValue("value"), "pear");

    def test_create(self):
        pass


    def test_invalidIndex(self):
        with self.assertRaises(sgprops.InvalidIndexString):
            parsed = sgprops.readProps(testData("bad-index.xml"))

    def test_include(self):
        parsed = sgprops.readProps(testData("props2.xml"))

        # test that value in main file over-rides the one in the include
        self.assertEqual(parsed.getValue("value"), 33)

        # but these come from the included file
        self.assertEqual(parsed.getValue("value[1]"), 43)
        self.assertEqual(parsed.getValue("value[2]"), 44)

        subNode = parsed.getChild("sub")
        widgets = subNode.getChildren("widget")
        self.assertEqual(len(widgets), 4)

        self.assertEqual(widgets[0].value, 42)
        self.assertEqual(widgets[0].index, 0)

        self.assertEqual(widgets[1].value, 43)
        self.assertEqual(widgets[1].index, 1)

        self.assertEqual(widgets[2].value, 44)
        self.assertEqual(widgets[2].index, 2)

        self.assertEqual(widgets[3].value, 99)
        self.assertEqual(widgets[3].index, 100)

if __name__ == '__main__':
    unittest.main()
