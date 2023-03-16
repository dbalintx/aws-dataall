import setuptools

__pkg_name__ = 'data.all-deploy'
__version__ = '1.4.2'
__author__ = 'AWS Professional Services'

setuptools.setup(
    name=__pkg_name__,
    version=__version__,
    description='data.all deployment package',
    author=__author__,
    package_dir={'': 'stacks'},
    packages=setuptools.find_packages(where='stacks'),
    python_requires='>=3.7',
)
