from setuptools import setup, find_packages
import os


CLASSIFIERS = [
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Software Development',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
]

setup(
    author="Elias Showk",
    author_email="elias.showk@gmail.com",
    name='django-ucengine',
    version='0.1',
    description='real-time channels for django users',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    url='https://github.com/commonecoute/django-ucengine',
    license='GNU AGPL v3',
    platforms=['Linux'],
    classifiers=CLASSIFIERS,
    # use pip install -r requirements.txt
    install_requires = ['distribute'],
    packages=find_packages(),
    include_package_data=True,
    package_data={},
    zip_safe = True
)
