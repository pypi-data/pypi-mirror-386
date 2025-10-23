import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "pepperize.projen-awscdk-app-ts",
    "version": "0.0.779",
    "description": "This project provides a projen project type providing presets for an AWS CDK construct library project",
    "license": "MIT",
    "url": "https://github.com/pepperize/projen-awscdk-app-ts.git",
    "long_description_content_type": "text/markdown",
    "author": "Patrick Florek<patrick.florek@gmail.com>",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/pepperize/projen-awscdk-app-ts.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "pepperize_projen_awscdk_app_ts",
        "pepperize_projen_awscdk_app_ts._jsii"
    ],
    "package_data": {
        "pepperize_projen_awscdk_app_ts._jsii": [
            "projen-awscdk-app-ts@0.0.779.jsii.tgz"
        ],
        "pepperize_projen_awscdk_app_ts": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "jsii>=1.116.0, <2.0.0",
        "projen>=0.91.4, <0.92.0",
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
