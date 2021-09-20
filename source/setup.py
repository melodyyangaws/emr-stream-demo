######################################################################################################################
# Copyright 2020-2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.                                      #
#                                                                                                                   #
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance    #
# with the License. A copy of the License is located at                                                             #
#                                                                                                                   #
#     http://www.apache.org/licenses/LICENSE-2.0                                                                    #
#                                                                                                                   #
# or in the 'license' file accompanying this file. This file is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES #
# OR CONDITIONS OF ANY KIND, express o#implied. See the License for the specific language governing permissions     #
# and limitations under the License.  																				#                                                                              #
######################################################################################################################

import setuptools

try:
    with open("../README.md") as fp:
        long_description = fp.read()
except IOError as e:
    long_description = ''

setuptools.setup(
    name="emr-stream-demo",
    version="1.0.0",

    description="A CDK Python app for Spark Structured Streaming ETL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    author="meloyang",

    package_dir={"": "./"},
    packages=setuptools.find_packages(where="./"),

    install_requires=[
        "aws-cdk.core==1.122.0",
        "aws-cdk.aws_iam==1.122.0",
        "aws-cdk.aws_eks==1.122.0",
        "aws-cdk.aws_ec2==1.122.0",
        "aws-cdk.aws_s3==1.122.0",
        "aws-cdk.aws_s3_deployment==1.122.0",
        "aws_cdk.aws_elasticloadbalancingv2==1.122.0",
        "aws-cdk.aws-emrcontainers==1.122.0",
        "aws-cdk.aws-emr==1.122.0",
        "aws-cdk.aws_msk==1.122.0",
        "aws-cdk.aws-cloud9==1.122.0",
        "pyyaml==5.4"
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: MIT License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
