from setuptools import setup, find_packages
import sitetool

setup(

    name = 'sittool',
    package = 'sitetool',
    version = sitetool.APP_VERSION,

    author = 'Jose Juan Montes, Pablo Arias',
    author_email = 'jjmontes@gmail.com',

    packages = find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),

    zip_safe=False,
    include_package_data=True,
    package_data = {
        #'sitetool': ['*.template']
    },

    url='https://github.com/jjmontesl/sitetool',
    license='LICENSE.txt',
    description='Tool to manage website deployments and development',
    long_description="SiteTool manages information about Joomla deployments and provides methods to backup and deploy Joomla sites across different staging environments.",

    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Database',
        'Topic :: Utilities',
    ],

    install_requires = [
        "pyyaml >= 5.1",
        "fs >= 0.3.0",
        "dateutils >= 0.6.6",
        "fabric >= 2.4.0",
        "humanize >= 0.5.1",
        "requests >= 2.22.0",
        "requests_html >= 0.10.0",
        "pathspec >= 0.5.9"
    ],

    entry_points={'console_scripts': ['sit=sitetool.core.bootstrap:main']},
)

