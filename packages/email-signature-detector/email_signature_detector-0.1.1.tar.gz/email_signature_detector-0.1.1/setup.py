
from setuptools import setup, find_packages

setup(
    name='email_signature_detector',
    version='0.1.1',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'numpy',
        'onnxruntime',
        'transformers',
    ],
    author='Numeo AI Team',
    author_email='team@numeo.ai',
    description='A library to predict email signatures using an ONNX model.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/numeo-ai/email-signature-detector',
    include_package_data=True,
    package_data={
        'email_signature_detector': ['model/*', 'model/tokenizer/*'],
    },
)