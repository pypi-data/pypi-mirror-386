# setup.py
from setuptools import setup, find_packages

setup(
    name='gorjeh-tomato',  # نام پکیجی که کاربر با 'pip install' دانلود می‌کند
    version='0.1.1',  # نسخه اولیه پکیج
    author='Your Name',
    author_email='your.email@example.com',
    description='A fast Python library for calculating circle areas, named Gorjeh (Tomato).',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/YourUsername/tomato',  # آدرس گیت‌هاب پروژه (اختیاری)
    packages=find_packages(), # به setuptools می‌گوید پوشه 'tomato' را پیدا و پکیج کند
    install_requires=[
        'math', # اگرچه math پکیج داخلی است، اما می‌توان آن را به عنوان نمونه قرار داد.
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)