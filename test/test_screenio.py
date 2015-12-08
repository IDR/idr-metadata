import unittest
from cStringIO import StringIO
from ConfigParser import ConfigParser, NoOptionError

from pyidr.screenio import ScreenWriter


class TestScreenWriter(unittest.TestCase):

    def setUp(self, screen_name=None):
        fout = StringIO()
        self.name, self.rows, self.columns, self.fields = "Foo", 3, 4, 2
        self.size = self.rows * self.columns
        self.all_field_values = []
        self.extra_kv = {"Dimensions": "ZCT"}
        kwargs = {"screen_name": screen_name} if screen_name else {}
        writer = ScreenWriter(
            self.name, self.rows, self.columns, self.fields, **kwargs
        )
        self.screen_name = screen_name
        for i in xrange(self.size):
            field_values = ["%s_%02d_%d.fake" % (self.name, i, _)
                            for _ in xrange(self.fields)]
            self.all_field_values.append(field_values)
            writer.add_well(field_values, extra_kv=self.extra_kv)
        writer.write(fout)
        fout.seek(0)
        self.cp = ConfigParser()
        self.cp.readfp(fout)

    def test_sections(self):
        self.assertEqual(
            self.cp.sections(),
            ['Plate'] + ['Well %d' % _ for _ in xrange(self.size)]
        )

    def test_plate(self):
        sec = 'Plate'
        self.assertTrue(self.cp.has_section(sec))
        for k, v in [
                ("Name", self.name),
                ("Rows", self.rows),
                ("Columns", self.columns),
                ("Fields", self.fields),
        ]:
            self.assertTrue(self.cp.has_option(sec, k))
            self.assertEqual(self.cp.get(sec, k), str(v))
        if self.screen_name:
            self.assertEqual(self.cp.get(sec, "ScreenName"), self.screen_name)
        else:
            self.assertRaises(NoOptionError, self.cp.get, sec, "ScreenName")

    def test_wells(self):
        for i in xrange(self.rows):
            for j in xrange(self.columns):
                idx = i * self.columns + j
                sec = 'Well %d' % idx
                self.assertTrue(self.cp.has_section(sec))
                for k, v in [("Row", i), ("Column", j)]:
                    self.assertTrue(self.cp.has_option(sec, k))
                    self.assertEqual(self.cp.get(sec, k), str(v))
                for f in xrange(self.fields):
                    k = 'Field_%d' % f
                    self.assertTrue(self.cp.has_option(sec, k))
                    self.assertEqual(self.cp.get(sec, k),
                                     self.all_field_values[idx][f])
                    for ek, ev in self.extra_kv.iteritems():
                        self.assertTrue(self.cp.has_option(sec, ek))
                        self.assertEqual(self.cp.get(sec, ek), ev)


class TestScreenWriterName(TestScreenWriter):

    def setUp(self):
        super(TestScreenWriterName, self).setUp(screen_name="FooScreen")


def load_tests(loader, tests, pattern):
    test_cases = (TestScreenWriter, TestScreenWriterName)
    suite = unittest.TestSuite()
    for tc in test_cases:
        suite.addTests(loader.loadTestsFromTestCase(tc))
    return suite


if __name__ == "__main__":
    suite = load_tests(unittest.defaultTestLoader, None, None)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
