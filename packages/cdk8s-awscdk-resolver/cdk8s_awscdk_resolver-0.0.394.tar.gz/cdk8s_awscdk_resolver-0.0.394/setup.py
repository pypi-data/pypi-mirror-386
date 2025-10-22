import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "cdk8s-awscdk-resolver",
    "version": "0.0.394",
    "description": "@cdk8s/awscdk-resolver",
    "license": "Apache-2.0",
    "url": "https://github.com/cdk8s-team/cdk8s-awscdk-resolver.git",
    "long_description_content_type": "text/markdown",
    "author": "Amazon Web Services",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/cdk8s-team/cdk8s-awscdk-resolver.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "cdk8s_awscdk_resolver",
        "cdk8s_awscdk_resolver._jsii"
    ],
    "package_data": {
        "cdk8s_awscdk_resolver._jsii": [
            "awscdk-resolver@0.0.394.jsii.tgz"
        ],
        "cdk8s_awscdk_resolver": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "aws-cdk-lib>=2.195.0, <3.0.0",
        "cdk8s>=2.68.91, <3.0.0",
        "constructs>=10.3.0, <11.0.0",
        "jsii>=1.116.0, <2.0.0",
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
