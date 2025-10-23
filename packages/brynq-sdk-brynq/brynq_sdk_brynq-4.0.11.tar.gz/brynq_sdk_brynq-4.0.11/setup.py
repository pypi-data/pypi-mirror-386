from setuptools import find_namespace_packages, setup

setup(
    name='brynq_sdk_brynq',
    version='4.0.11',
    description='BrynQ SDK for the BrynQ.com platform',
    long_description='BrynQ SDK for the BrynQ.com platform',
    author='BrynQ',
    author_email='support@brynq.com',
    packages=find_namespace_packages(include=['brynq_sdk*']),
    license='BrynQ License',
    install_requires=[
        'requests>=2,<=3'
    ],
    zip_safe=False,
)
