from setuptools import setup, find_packages

setup(
    name='sgFCMed_test',
    version='0.0.1',
    description='Simply Lovely',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Nawawan Thaichim',
    author_email='richwoon09@email.com',
    packages=find_packages(),
    install_requires=[
        "pytest"
    ],
    license='MIT',
    python_requires='>=3.7',
)