import doctest
import os
import re
import unittest
import zope.app.testing.functional


Layer = zope.app.testing.functional.ZCMLLayer(
    os.path.join(os.path.dirname(__file__), 'ftesting.zcml'),
    __name__, 'gocept.form.layer', allow_teardown=True)


# Strip out u'' literals in doctests, adapted from
# <https://stackoverflow.com/a/56507895>.
class Py23OutputChecker(doctest.OutputChecker, object):
    RE = re.compile(r"(\W|^)[uU]([rR]?[\'\"])", re.UNICODE)

    def remove_u(self, want, got):
        return (re.sub(self.RE, r'\1\2', want),
                re.sub(self.RE, r'\1\2', got))

    def check_output(self, want, got, optionflags):
        want, got = self.remove_u(want, got)
        return super(Py23OutputChecker, self).check_output(
            want, got, optionflags)

    def output_difference(self, example, got, optionflags):
        example.want, got = self.remove_u(example.want, got)
        return super(Py23OutputChecker, self).output_difference(
            example, got, optionflags)


def FunctionalDocFileSuite(*paths, **kw):
    try:
        layer = kw['layer']
    except KeyError:
        layer = Layer
    else:
        del kw['layer']
    kw['package'] = doctest._normalize_module(kw.get('package'))
    kw['checker'] = Py23OutputChecker()
    test = zope.app.testing.functional.FunctionalDocFileSuite(
        *paths, **kw)
    test.layer = layer
    return test


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(FunctionalDocFileSuite(
        'base.txt',
        'confirm-action.txt',
        'destructive-action.txt',
        'grouped.txt',
        'multiple-constraints.txt'
    ))
    return suite
