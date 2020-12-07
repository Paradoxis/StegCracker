# Inherit from the base Alpine image
FROM "python:3.8-alpine"

# Image metadata
LABEL name="StegCracker"
LABEL description="Steganography brute-force utility" 
LABEL version="v2.0.9"
LABEL maintainer="Paradoxis" 
LABEL website="https://github.com/Paradoxis/StegCracker/tree/v2.0.9"
LABEL license="MIT"

# Install dependencies
RUN apk update
RUN apk add steghide bash tar curl \
  --repository https://dl-3.alpinelinux.org/alpine/edge/testing

# Install default wordlist
RUN mkdir -p /usr/local/bin/ /usr/share/wordlists/

RUN curl -s -L -o \
  /usr/share/wordlists/rockyou.txt.tar.gz \
  https://github.com/danielmiessler/SecLists/raw/master/Passwords/Leaked-Databases/rockyou.txt.tar.gz

RUN tar xzf \
  /usr/share/wordlists/rockyou.txt.tar.gz \
  -C /usr/share/wordlists/

# Install StegCracker
WORKDIR /tmp/
COPY stegcracker /tmp/stegcracker
COPY setup.py README.md /tmp/
RUN pip install .
RUN rm -rf /tmp/stegcracker /tmp/setup.py /tmp/README.md

# Set data directory
VOLUME /data
WORKDIR /data

# Entrypoint
ENTRYPOINT ["/usr/local/bin/stegcracker"]
