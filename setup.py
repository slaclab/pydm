import versioneer
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path, environ

cur_dir = path.abspath(path.dirname(__file__))

with open(path.join(cur_dir, 'requirements.txt')) as f:
    requirements = f.read().split()

with open(path.join(cur_dir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Remove the 'optional' requirements
optional = ('PyQt5', 'PySide', 'psutil', 'pcaspy', 'pyepics')
for package in optional:
    if package in requirements:
        requirements.remove(package)

extras_require = {
    'PySide': ['PySide'],
    'pyepics': ['pyepics'],
    'perf': ['psutil'],
    'test': ['codecov', 'pytest', 'pytest-cov', 'coverage', 'coveralls']
}

if "CONDA_PREFIX" not in environ:
    extras_require['PyQt5'] = ['PyQt5']
else:
    print("******************************************************************")
    print("*                              WARNING                           *")
    print("******************************************************************")
    print("Installing at an Anaconda Environment, to avoid naming conflicts ")
    print("make sure you do:")
    print("conda install pyqt=5")
    print("******************************************************************")
    print("For more info please check: ")
    print("https://github.com/ContinuumIO/anaconda-issues/issues/1554")
    print("******************************************************************")

extras_require['all'] = sorted(set(sum(extras_require.values(), [])))
# Preference for PyQt5 if you select ALL...
extras_require['all'].remove('PySide')

setup(
    name='pydm',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    # Author details
    author='SLAC National Accelerator Laboratory',

    packages=find_packages(),
    package_dir={'pydm':'pydm', 'pydm_launcher':'pydm_launcher'},
    description='Python Display Manager',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/slaclab/pydm',
    entry_points={
        'gui_scripts': [
            'pydm=pydm_launcher.main:main'
        ]
    },
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
        'Programming Language :: Python :: 3.6',
    ]
)
