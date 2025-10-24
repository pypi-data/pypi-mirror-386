# -*- coding: utf-8 -*-
import os
from io import open
from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.en.md"), "r", encoding="utf-8") as fobj:
    long_description = fobj.read()

with open(os.path.join(here, "requirements.txt"), "r", encoding="utf-8") as fobj:
    requires = [x.strip() for x in fobj.readlines() if x.strip()]

setup(
    name="kafka-admin-service",
    version="0.2.18",
    description="KAFKA管理类，提供用户创建、删除、列表查询、修改密码，提供主题创建、删除、列表查询，提供权限创建、删除、列表查询等基础管理功能。",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="rRR0VrFP",
    maintainer="rRR0VrFP",
    license="MIT",
    license_files=("LICENSE",),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords=["kafka admin service", "kafka admin client"],
    install_requires=requires,
    packages=find_packages("."),
    zip_safe=False,
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "kafka-admin-server = kafka_admin_service.server:application_ctrl",
        ]
    },
)
