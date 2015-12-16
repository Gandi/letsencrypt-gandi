import sys

from setuptools import setup
from setuptools import find_packages


version = '0.0.1.dev0'

install_requires = [
    'setuptools',  # pkg_resources
]

if sys.version_info < (2, 7):
    install_requires.append('mock<1.1.0')
else:
    install_requires.append('mock')



setup(
    name='letsencrypt-gandi',
    version=version,
    description="GANDI plugin for Let's Encrypt client",
    url='https://github.com/Gandi/letsencrypt-gandi',
    author="GANDI Developers",
    author_email='feedback@gandi.net',
    license='Apache License 2.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Security',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Networking',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],

    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    entry_points={
        'letsencrypt.plugins': [
            'gandi-shs = letsencrypt_gandi.shs:GandiSHSConfigurator',
        ],
    },
)
