from setuptools import setup, find_packages

setup(
    name='aws-cli-tool',
    version='0.1.0',
    description='CLI tool to query AWS EC2 resource usage',
    author='Your Name',
    packages=find_packages(),
    install_requires=[
        'boto3',
    ],
    entry_points={
        'console_scripts': [
            'aws-query=aws_cli_tool.aws_query:main'
        ]
    },
    python_requires='>=3.7',
)
    
#entry_points creates the aws-query command, so users just type aws-query in their terminal.
#aws_cli_tool.aws_query:main tells Python to run the main() function inside aws_query.py.

