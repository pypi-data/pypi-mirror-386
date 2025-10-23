# setup.py

from setuptools import setup, find_packages

setup(
    name='paykad',  # نام پکیج
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A simple, modern abstraction layer for Python GUI development (based on Tkinter).',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/YourUsername/paykad',
    
    # اطمینان از قرار گرفتن پوشه paykad در پکیج
    packages=find_packages(),
    
    # Tkinter جزو پکیج‌های استاندارد پایتون است و نیازی به نصب ندارد
    install_requires=[], 
    
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: User Interfaces',
    ],
    python_requires='>=3.6',
)