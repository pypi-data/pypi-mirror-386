from setuptools import setup, find_packages

setup(
    name='nltkbleu',
    version='0.1.1',
    author='pixelpilot24',
    author_email='pixelpilot24@gmail.com',
    description='A nltk scoring and text utility module with TensorFlow and NLP tools.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/nltkbleu',
    packages=find_packages(),
    license='MIT',
    install_requires=[
        'numpy',
        'pandas',
    ],
    python_requires='>=3.7',
)
