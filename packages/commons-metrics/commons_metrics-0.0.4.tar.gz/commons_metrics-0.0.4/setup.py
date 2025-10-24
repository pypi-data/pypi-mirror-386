from setuptools import setup, find_packages

setup(
    name='commons_metrics',
    version='0.0.4',
    description='A simple library for basic statistical calculations',
    #long_description=open('USAGE.md').read(),
    #long_description_content_type='text/markdown',
    author='Bancolombia',
    author_email='omar.david.pino@email.com',
    packages=find_packages(),
    install_requires=[
        "boto3"
    ],
    license='MIT',
    python_requires='>=3.7',
)
#pypi-AgEIcHlwaS5vcmcCJGU1OTQxZWMxLTY0MmQtNDU0Ni05MGZkLWE0NjVlNjRkZmY1MgACKlszLCJlZjE2NWIwZS1jYTIzLTRiYzgtYTY4YS0xZTlmYTJhOTE3N2QiXQAABiBwZywp_gME-Ebk9x9eMMKnD1jGEnbL7TOdFOGzzTw1Hw