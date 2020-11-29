from itertools import chain
from setuptools import find_packages, setup

from naturtag import __version__

extras_require = {  # noqa
    'app': ['kivy>=1.11', 'kivymd~=0.104.1', 'kivy-garden.contextmenu', 'pygments'],
    'build': ['coveralls', 'twine', 'wheel'],
    'dev': [
        'black==20.8b1',
        'flake8',
        'isort',
        'mypy',
        'pre-commit',
        'pytest>=5.0',
        'pytest-cov',
        'Sphinx>=3.0',
        'kivy_examples',
        'memory_profiler',
        'prettyprinter',
        'Sphinx~=3.2.1',
        'sphinx-rtd-theme',
        'sphinxcontrib-apidoc',
    ],
}
extras_require['all'] = list(chain.from_iterable(extras_require.values()))
extras_require['app-win'] = [
    'pypiwin32',
    'kivy_deps.sdl2',
    'kivy_deps.gstreamer',
    'kivy_deps.angle',
]
extras_require['all-win'] = extras_require['all'] + extras_require['app-win']

# To install kivy dev version on python 3.8:
# pip install kivy[base] kivy_examples --pre --extra-index-url https://kivy.org/downloads/simple/

setup(
    name='naturtag',
    version=__version__,
    packages=find_packages(),
    install_requires=[
        'appdirs',
        'attrs',
        'Click>=7.0',
        'click-help-colors',
        'pillow>=7.0',
        'pyexiv2',
        'python-dateutil',
        'pyinaturalist==0.12.0.dev68',
        'pyyaml',
        'requests',
        'requests-cache',
        'xmltodict',
    ],
    extras_require=extras_require,
    entry_points={
        'console_scripts': [
            'naturtag=naturtag.cli:main',
            'nt=naturtag.cli:main',
        ],
        'gui_scripts': [
            'naturtag-app=naturtag.app.app:main',
        ],
    },
)
