from distutils.core import setup
import py2exe

OPTIONS = {'excludes': ['_ssl', '_hashlib', 'bz2', 'doctest', 'pdb',
                        'unicodedata', 'unittest', 'difflib', 'inspect'],
           'compressed': True, 'bundle_files': 3}

setup(name='Network Remote', version='0.31', author='William McBrine',
      windows=[{'script': 'Network Remote.pyw',
                'icon_resources': [(0, 'remote.ico')]}],
      data_files=[('.', ['remote.ico'])],
      options={'py2exe': OPTIONS})
