from setuptools import setup, find_packages

setup(
    packages=find_packages(),
    package_data={
        'dc_chat_exporter': ['template.html'],
    },
    include_package_data=True,
)