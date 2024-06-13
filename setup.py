from setuptools import setup, find_packages



setup(
    name='f0ma',
    version='0.1',
    py_modules=["code"],
    author='foma',
    author_email='fomaximenkov@gmail.com',
    description='Мощное средство для сбора логов с различных устройств, предоставляющие инструменты для эффективного мониторинга и анализа системных событий',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/fffomiii/pythonProject',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'appdirs==1.4.4',
        'mpmath==1.3.0',
        'pygame==2.5.2',
        'pyparsing==3.1.1',
        'sympy==1.12',
        'systemd-python==235',
        'tk==0.1.0',
        'watchdog==3.0.0'
    ],
    entry_points={
        'console_scripts': [
            'f0ma=code:main_entry',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
