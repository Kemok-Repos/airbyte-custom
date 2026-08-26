#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


from setuptools import find_packages, setup

# Versiones pineadas a las que ya corren en la imagen desplegada (`pip freeze` sobre
# `airbyte/destination-typesense:kemok`, 26 ago 2026). La imagen no se reconstruia desde
# feb 2026: sin pin, el proximo `docker build` resolveria ambas a la version del dia y el
# rebuild traeria seis meses de saltos de dependencias que nadie eligio, encima del unico
# conector que atiende a Guatecompras, Explora y La Hora a la vez.
MAIN_REQUIREMENTS = ["airbyte-cdk==0.30.3", "typesense==0.15.1"]

TEST_REQUIREMENTS = ["pytest~=6.1", "typesense==0.15.1"]

setup(
    name="destination_typesense",
    description="Destination implementation for Typesense.",
    author="Airbyte",
    author_email="contact@airbyte.io",
    packages=find_packages(),
    install_requires=MAIN_REQUIREMENTS,
    package_data={"": ["*.json"]},
    extras_require={
        "tests": TEST_REQUIREMENTS,
    },
)
