from setuptools import setup


setup(
    name = 'gocept.form',
    version='0.9.0',
    author = "Christian Zagrodnick",
    author_email = "cz@gocept.com",
    description = "Extensions for zope.formlib",
    long_description = '\n\n'.join(
        open(name).read()
        for name in ['README.txt', 'CHANGES.txt']),
    license = "ZPL 2.1",
    url='http://pypi.python.org/pypi/gocept.form',

    include_package_data = True,
    zip_safe = False,

    install_requires = [
        'zope.interface',
        'zope.component',
        'zope.contentprovider',
        'zope.viewlet',
    ],
    extras_require = dict(
        test=[
              'zope.testbrowser',
              'zope.app.testing',
              'zope.app.zcmlfiles',
              'zope.viewlet!=3.4.1',
               'z3c.pagelet',
             ],
        formlib=[
            'zope.browserpage',
            'zope.formlib',
        ],
        z3cform=['z3c.form',
                 'z3c.pagelet'
                ])
    )
