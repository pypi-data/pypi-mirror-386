from setuptools import setup

setup(
    name='vm_custom_package',
    version='0.1.5.113',
    packages=['vm_custom_package'],
    include_package_data=True,
    install_requires=[
        "python-telegram-bot>=21.2",
        "psutil>=5.9.8",
        "requests>=2.32.2",
        "jdatetime>=5.0.0",
        "django>=4.2.13",
        "cryptography>=43.0.0",
        "loguru>=0.7.2",
        "beautifulsoup4>=4.13.4",
        "selenium>=4.31.0",
        "selenium-wire>=5.1.0",
    ],
)

