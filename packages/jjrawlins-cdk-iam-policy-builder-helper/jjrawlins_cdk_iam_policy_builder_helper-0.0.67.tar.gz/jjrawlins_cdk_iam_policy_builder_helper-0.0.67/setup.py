import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "jjrawlins-cdk-iam-policy-builder-helper",
    "version": "0.0.67",
    "description": "A CDK construct that helps build IAM policies using the AWS IAM Policy Builder dump. Normally it is better to use cdk-iam-floyd, However, I found that cdk-iam-floyd currently is not jsii compliant so I wasn't able to use it in my jsii compliant projects in languages that are not typescript or python.",
    "license": "Apache-2.0",
    "url": "https://github.com/JaysonRawlins/cdk-iam-policy-builder-helper.git",
    "long_description_content_type": "text/markdown",
    "author": "Jayson Rawlins<JaysonJ.Rawlins@gmail.com>",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/JaysonRawlins/cdk-iam-policy-builder-helper.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "jjrawlins_cdk_iam_policy_builder_helper._jsii"
    ],
    "package_data": {
        "jjrawlins_cdk_iam_policy_builder_helper._jsii": [
            "cdk-iam-policy-builder-helper@0.0.67.jsii.tgz"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "aws-cdk-lib>=2.85.0, <3.0.0",
        "constructs>=10.0.5, <11.0.0",
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
