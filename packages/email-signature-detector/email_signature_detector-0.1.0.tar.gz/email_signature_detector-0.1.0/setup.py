
from setuptools import setup, find_packages

setup(
    name='email_signature_detector',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'numpy',
        'onnxruntime',
        'transformers',
    ],
    author='Bexruz Raxmonov',
    author_email='bexruz.raxmonov@gmail.com',
    description='A library to predict email signatures using an ONNX model.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/BexruzRaxmonov/email-parser-training-pipline',
    include_package_data=True,
    package_data={
        'email_signature_detector': ['model/*', 'model/tokenizer/*'],
    },
)