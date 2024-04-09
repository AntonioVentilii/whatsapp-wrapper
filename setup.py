from setuptools import find_packages, setup

setup(
    name='whatsapp_wrapper',
    version='0.1.4',
    author='Antonio Ventilii',
    author_email='antonioventilii@gmail.com',
    license='MIT',
    description='Integration layer for WhatsApp Cloud API with Firestore for easy message storage and management.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/AntonioVentilii/whatsapp-wrapper',
    project_urls={
        'Source Code': 'https://github.com/AntonioVentilii/whatsapp-wrapper',
        'Issue Tracker': 'https://github.com/AntonioVentilii/whatsapp-wrapper/issues',
    },
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    keywords='WhatsApp, Firestore, API, integration, messaging',
    install_requires=[
        'requests',
        'firestore-wrapper',
        'pydub',
        'ffmpeg-downloader',
        'ffmpeg-python',
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
        ],
    },
)
