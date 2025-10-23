import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "cdk-certbot-dns-route53",
    "version": "1.2.636",
    "description": "Create Cron Job Via Lambda, to update certificate and put it to S3 Bucket.",
    "license": "Apache-2.0",
    "url": "https://github.com/neilkuan/cdk-certbot-dns-route53.git",
    "long_description_content_type": "text/markdown",
    "author": "Neil Kuan<guan840912@gmail.com>",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/neilkuan/cdk-certbot-dns-route53.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "cdk_certbot_dns_route53",
        "cdk_certbot_dns_route53._jsii"
    ],
    "package_data": {
        "cdk_certbot_dns_route53._jsii": [
            "cdk-certbot-dns-route53@1.2.636.jsii.tgz"
        ],
        "cdk_certbot_dns_route53": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "aws-cdk.aws-events-targets>=1.76.0, <2.0.0",
        "aws-cdk.aws-events>=1.76.0, <2.0.0",
        "aws-cdk.aws-iam>=1.76.0, <2.0.0",
        "aws-cdk.aws-lambda>=1.76.0, <2.0.0",
        "aws-cdk.aws-logs>=1.76.0, <2.0.0",
        "aws-cdk.aws-route53>=1.76.0, <2.0.0",
        "aws-cdk.aws-s3>=1.76.0, <2.0.0",
        "aws-cdk.core>=1.204.0, <2.0.0",
        "constructs>=3.2.27, <4.0.0",
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
