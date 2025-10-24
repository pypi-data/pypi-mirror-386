import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "cdk-ec2-key-pair",
    "version": "5.0.0",
    "description": "CDK Construct for managing EC2 key pairs",
    "license": "Apache-2.0",
    "url": "https://github.com/udondan/cdk-ec2-key-pair",
    "long_description_content_type": "text/markdown",
    "author": "Daniel Schroeder",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/udondan/cdk-ec2-key-pair.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "cdk_ec2_key_pair",
        "cdk_ec2_key_pair._jsii"
    ],
    "package_data": {
        "cdk_ec2_key_pair._jsii": [
            "cdk-ec2-key-pair@5.0.0.jsii.tgz"
        ],
        "cdk_ec2_key_pair": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "aws-cdk-lib>=2.219.0, <3.0.0",
        "constructs>=10.0.0, <11.0.0",
        "jsii>=1.117.0, <2.0.0",
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
        "License :: OSI Approved"
    ],
    "scripts": []
}
"""
)

with open("README.md", encoding="utf8") as fp:
    kwargs["long_description"] = fp.read()


setuptools.setup(**kwargs)
