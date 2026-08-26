FROM python:3.9.11-alpine3.15 as base

# build and load all requirements
FROM base as builder
WORKDIR /airbyte/integration_code

# upgrade pip to the latest version
RUN apk --no-cache upgrade \
    && pip install --upgrade pip \
    && apk --no-cache add tzdata build-base


COPY setup.py ./
# install necessary packages to a temporary folder
RUN pip install --prefix=/install .

# build a clean environment
FROM base
WORKDIR /airbyte/integration_code

# copy all loaded and built libraries to a pure basic image
COPY --from=builder /install /usr/local
# add default timezone settings
COPY --from=builder /usr/share/zoneinfo/Etc/UTC /etc/localtime
RUN echo "Etc/UTC" > /etc/timezone

# bash is installed for more convenient debugging.
RUN apk --no-cache add bash

# copy payload code only
COPY main.py ./
COPY destination_typesense ./destination_typesense

ENV AIRBYTE_ENTRYPOINT "python /airbyte/integration_code/main.py"
ENTRYPOINT ["python", "/airbyte/integration_code/main.py"]

# El label queda igual al tag con el que se construye. `kemok` es un tag mutable: no dice
# cuando se armo la imagen ni de que commit salio, asi que `docker inspect` sobre la imagen
# desplegada no permitia distinguir una build de otra. Construir con
#   docker build --build-arg VERSION=kemok-2026-08-26 -t airbyte/destination-typesense:kemok-2026-08-26 .
# deja el label y el tag diciendo lo mismo. Sin --build-arg se comporta como antes.
ARG VERSION=kemok
LABEL io.airbyte.version=$VERSION
LABEL io.airbyte.name=airbyte/destination-typesense
