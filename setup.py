from setuptools import setup, find_packages


with open("project-description.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup_args = dict(
    name='TradingBot',
    version='0.1.0',
    description='A Python toolkit for strategy design, backtesting, and algorithm trading',
    long_description_content_type="text/markdown",
    long_description=long_description,
    license='MIT',
    packages=find_packages(),
    author='Dayu Yang',
    author_email='dayu@udel.edu',
    keywords=['Stock', 'Trading'],
    url='https://github.com/dayuyang1999/TradingBot', 
    download_url='https://pypi.org/project/TradingBot'
)


install_requires = [
    'alpaca-trade-api>=2.0.0,<3.0.0',
    'jupyter'
    ]

if __name__ == '__main__':
    setup(**setup_args, install_requires=install_requires)
