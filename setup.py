import versioneer
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

cur_dir = path.abspath(path.dirname(__file__))

with open(path.join(cur_dir, 'requirements.txt')) as f:
    requirements = f.read().split()

# Remove the 'optional' requirements
optional = ('PyQt5', 'PyQt4', 'PySide', 'psutil', 'pcaspy', 'pyepics')
for package in optional:
    if package in requirements:
        requirements.remove(package)

extras_require = {
    'PyQt5': ['PyQt5'],
    'PyQt4': ['PyQt4'],
    'PySide': ['PySide'],
    'pyepics': ['pyepics'],
    'perf': ['psutil'],
    'testing-ioc': ['pcaspy'],
    'test': ['codecov', 'pytest', 'pytest-cov', 'coverage', 'coveralls', 'pcaspy']
}

extras_require['all'] = sorted(set(sum(extras_require.values(), [])))
# Preference for PyQt5 if you select ALL...
extras_require['all'].remove('PyQt4')
extras_require['all'].remove('PySide')

setup(
    name='pydm',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    # Author details
    author='SLAC National Accelerator Laboratory',

    packages=find_packages(),
    description='Python Display Manager',
    url='https://github.com/slaclab/pydm',
    scripts=['scripts/pydm', 'scripts/testing-ioc', 'scripts/access_rules.as'],
    license='BSD',

    install_requires=requirements,
    extras_require=extras_require,
    include_package_data=True,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)
