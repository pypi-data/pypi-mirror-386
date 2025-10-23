import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "aws-cdk.cloud-assembly-schema",
    "version": "48.16.0",
    "description": "Schema for the protocol between CDK framework and CDK CLI",
    "license": "Apache-2.0",
    "url": "https://github.com/aws/aws-cdk",
    "long_description_content_type": "text/markdown",
    "author": "Amazon Web Services",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/aws/aws-cdk-cli"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "aws_cdk.cloud_assembly_schema",
        "aws_cdk.cloud_assembly_schema._jsii"
    ],
    "package_data": {
        "aws_cdk.cloud_assembly_schema._jsii": [
            "cloud-assembly-schema@48.16.0.jsii.tgz"
        ],
        "aws_cdk.cloud_assembly_schema": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "jsii>=1.114.1, <2.0.0",
        "publication>=0.0.3",
        "typeguard>=2.13.3,<4.3.0"
    ],
    "classifiers": [
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Typing :: Typed",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved",
        "Framework :: AWS CDK",
        "Framework :: AWS CDK :: 2"
    ],
    "scripts": []
}
"""
)

with open("README.md", encoding="utf8") as fp:
    kwargs["long_description"] = fp.read()


setuptools.setup(**kwargs)
