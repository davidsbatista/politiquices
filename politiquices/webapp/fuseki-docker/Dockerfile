
FROM openjdk:11

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
       bash curl ca-certificates findutils coreutils pwgen \
    ; \
    rm -rf /var/lib/apt/lists/*

ENV FUSEKI_VERSION=3.16.0
ENV ASF_MIRROR=http://www.apache.org/dyn/mirrors/mirrors.cgi?action=download&filename=
ENV ASF_ARCHIVE=http://archive.apache.org/dist/

# Config and data
VOLUME /fuseki
ENV FUSEKI_BASE /fuseki

# Installation folder
ENV FUSEKI_HOME /jena-fuseki


WORKDIR /tmp

RUN curl --fail --silent --show-error --retry-connrefused --retry 3 --output fuseki.tar.gz $ASF_ARCHIVE/jena/binaries/apache-jena-fuseki-$FUSEKI_VERSION.tar.gz && \
     tar zxf fuseki.tar.gz && \
     mv apache-jena-fuseki* $FUSEKI_HOME && \
     rm fuseki.tar.gz* && \
     cd $FUSEKI_HOME && rm -rf fuseki.war && chmod 755 fuseki-server

# copy a custome 'shiro.ini' allowing connections from anywhere with auth
# this will allow to use the webapp to see any already created datasets
COPY shiro.ini $FUSEKI_BASE/shiro.ini

WORKDIR $FUSEKI_HOME
EXPOSE 3030
ENTRYPOINT ["/jena-fuseki/fuseki-server"]