import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "jjrawlins-cdk-git-tagger",
    "version": "0.0.57",
    "description": "CDK Aspect to tag resources with git metadata.  This provides a nice connection between the construct and the git repository.",
    "license": "Apache-2.0",
    "url": "https://github.com/JaysonRawlins/cdk-git-tagger.git",
    "long_description_content_type": "text/markdown",
    "author": "Jayson Rawlins<JaysonJ.Rawlins@gmail.com>",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/JaysonRawlins/cdk-git-tagger.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "jjrawlins_cdk_git_tagger",
        "jjrawlins_cdk_git_tagger._jsii"
    ],
    "package_data": {
        "jjrawlins_cdk_git_tagger._jsii": [
            "cdk-git-tagger@0.0.57.jsii.tgz"
        ],
        "jjrawlins_cdk_git_tagger": [
            "py.typed"
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
