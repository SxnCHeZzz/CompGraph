import unittest
from pathlib import Path
import math
import task1a
import task1b
import task2
import task3


class LSystemTests(unittest.TestCase):
    def test_lecture_examples(self):
        for path in (Path(__file__).parent / 'examples').glob('*.txt'):
            with self.subTest(example=path.name):
                axiom, angle, direction, rules = task1a.parse_lsystem(path.read_text(encoding='utf-8'))
                commands = task1a.generate(axiom, rules, 3, 12)
                segments = task1a.calculate_segments(commands, angle, direction)
                self.assertTrue(segments)
                fitted = task1a.fit_points([p for s in segments for p in s[:2]], 900, 600)
                self.assertTrue(all(29.99 <= x <= 870.01 and 29.99 <= y <= 570.01 for x,y in fitted))

    def test_rewriting_and_stack(self):
        axiom, angle, direction, rules = task1a.parse_lsystem('F 60 0\nF -> F-F++F-F')
        self.assertEqual(task1a.generate(axiom, rules, 0), 'F')
        for iteration in range(5):
            s = task1a.calculate_segments(task1a.generate(axiom,rules,iteration), angle,direction)
            self.assertEqual(len(s), 4 ** iteration)
        s = task1a.calculate_segments('F[+F]F', 90, 0)
        self.assertEqual(s[2][0], (1,0))
        self.assertAlmostEqual(s[1][1][1],1)
        self.assertEqual(s[1][2],1)
        for commands in ['F]', 'F[+F']:
            with self.assertRaises(ValueError):task1a.calculate_segments(commands, 30, 0)

    def test_randomness_and_tree(self):
        args = task1a.parse_lsystem((Path(__file__).parent/'examples'/'bush3.txt').read_text())
        axiom, angle, direction, rules = args
        commands = task1a.generate(axiom,rules,4)
        a = task1a.calculate_segments(commands,angle,direction,8,9)
        self.assertEqual(a,task1a.calculate_segments(commands,angle,direction,8,9))
        self.assertNotEqual(a,task1a.calculate_segments(commands,angle,direction,8,10))
        _,styles=task1b.build_tree(axiom,rules,4,angle,direction,8,9)
        self.assertEqual(len(styles),len(a))
        self.assertEqual(styles[0],(12,(110,65,30)))
        self.assertTrue(any(w<3 and color[1]>color[0] for w,color in styles))
        rules={'F':['F+F','F-F']}
        self.assertEqual(task1a.generate('F',rules,6,9),task1a.generate('F',rules,6,9))
        self.assertNotEqual(task1a.generate('F',rules,6,9),task1a.generate('F',rules,6,10))

    def test_invalid_input_and_limits(self):
        for text in ['', 'F 90', 'F nope 90', 'F 30 0\nAB -> F', 'F 30 0\ninvalid']:
            with self.assertRaises(ValueError):task1a.parse_lsystem(text)
        with self.assertRaises(ValueError):task1a.generate('F',{'F':['FFFFFFFFFF']},10)
        vertical = task1a.fit_points([(0,0),(0,10)],200,200)
        self.assertEqual(vertical[0][0],100)


class MountainTests(unittest.TestCase):
    def test_all_steps_and_endpoints(self):
        steps=task2.midpoint_displacement(10,seed=8)
        self.assertEqual(len(steps),11)
        for i,points in enumerate(steps):
            self.assertEqual(len(points),2**i+1)
            self.assertEqual(points[0],(0.,0.));self.assertEqual(points[-1],(1000.,0.))
            if i:self.assertEqual(points[::2],steps[i-1])
        self.assertEqual(steps,task2.midpoint_displacement(10,seed=8))
        self.assertNotEqual(steps,task2.midpoint_displacement(10,seed=9))

    def test_zero_roughness_and_formula(self):
        steps=task2.midpoint_displacement(6,0,left_height=10,right_height=30,length=100)
        self.assertTrue(all(abs(y-(10+x*.2))<1e-9 for x,y in steps[-1]))
        import random
        expected=random.Random(42).uniform(-.3*1000,.3*1000)
        self.assertAlmostEqual(task2.midpoint_displacement(1,seed=42)[1][1][1],expected)
        for kwargs in [{'iterations':15},{'roughness':-1},{'decay':0},{'length':0}]:
            with self.assertRaises(ValueError):task2.midpoint_displacement(**kwargs)


class BezierTests(unittest.TestCase):
    def test_endpoints_and_smooth_joins(self):
        points=[(10,20),(100,200),(250,50),(400,180),(500,100)]
        curves=task3.sample_spline(points)
        self.assertEqual(len(curves),4)
        for i,curve in enumerate(curves):
            self.assertEqual(curve[0],points[i]);self.assertEqual(curve[-1],points[i+1])
        for i in range(len(points)-2):
            left,right=task3.control_points(points,i),task3.control_points(points,i+1)
            for axis in (0,1):
                self.assertAlmostEqual(3*(left[3][axis]-left[2][axis]),3*(right[1][axis]-right[0][axis]))
        self.assertEqual(task3.sample_spline([]),[])
        self.assertEqual(task3.sample_spline([(1,1)]),[])
        two=task3.sample_spline([(0,0),(6,6)])[0]
        self.assertTrue(all(abs(x-y)<1e-9 for x,y in two))
        self.assertEqual(task3.nearest_point(points,100,200),1)
        self.assertIsNone(task3.nearest_point(points,900,900))
        self.assertTrue(all(math.isfinite(x) for point in task3.sample_spline([(0,0)]*4)[0] for x in point))


if __name__ == '__main__':
    unittest.main(verbosity=2)
