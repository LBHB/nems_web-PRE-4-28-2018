import codecs
import os.path
from setuptools import find_packages, setup

NAME = 'NEMS_WEB'

version = 'pre-alpha'

with codecs.open('README.md', encoding='utf-8') as f:
    long_description = f.read()

GENERAL_REQUIRES = [
        'numpy', 'scipy', 'matplotlib', 'flask', 'sqlalchemy', 'mpld3',
        'boto3', 'tensorflow', 'bokeh', 'flask-socketio', 'eventlet', 'bcrypt',
        'flask-WTF', 'flask-login', 'flask-bcrypt', 'seaborn', 'flask-assets',
        'pymysql',
        ]

# Additional dependency: NEMS (https://bitbucket.org/lbhb/nems)

setup(
    name=NAME,
    version=version,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=True,
    author='LBHB',
    author_email='lbhb.ohsu@gmail.com',
    description='Web Application for the Neural Encoding Model System',
    long_description=long_description,
    url='http://neuralprediction.org',
    install_requires=GENERAL_REQUIRES,
    classifiers=[],
)
