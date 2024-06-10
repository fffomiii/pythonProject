from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='pythonProject',
    version='0.1',
    author='f0ma',
    author_email='fomaximenkov@gmail.com',
    description='Мощное средство для сбора логов с различных устройств, предоставляющие инструменты для эффективного мониторинга и анализа системных событий',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/fffomiii/pythonProject',
    packages=find_packages(),
    install_requires=required,
    entry_points={
        'console_scripts': [
            'my_project=my_package.main:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
