from setuptools.command.install import install
from setuptools import setup, find_packages

class PostInstallCommand(install):
    def run(self):
        install.run(self)
        import DSE3_wrapper.downloader as dw
        dw.download_large_data()

setup(
    name='DSE3_wrapper',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'requests',
        'py7zr'
    ],
    cmdclass={
        'install': PostInstallCommand,
    },
    author='Your Name',
    description='A package with auto Google Drive data download',
)
