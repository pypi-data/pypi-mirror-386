#!/usr/bin/env python
from setuptools import find_namespace_packages, setup

package_name = "dbt-rabbit-bigquery"
package_version = "1.0.4"
description = """The Rabbit BigQuery adapter plugin for dbt"""

setup(
    name=package_name,
    version=package_version,
    description=description,
    long_description=description,
    long_description_content_type="text/markdown",
    author="Rabbit Team",
    author_email="success@followrabbit.ai",
    url="https://followrabbit.ai",
    packages=find_namespace_packages(include=["dbt", "dbt.*"]),
    include_package_data=True,
    install_requires=[
        "dbt-bigquery>=1.5.0,<2.0.0",
        "rabbit-bq-job-optimizer>=0.1.12",
    ],
    entry_points={
        "dbt.adapters": [
            "rabbitbigquery = dbt.adapters.rabbitbigquery",
        ],
    },
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)

