# Inherit from the base Alpine image
FROM "alpine:3.12.1"

# Image metadata
LABEL name="StegCracker"
LABEL description="Steganography brute-force utility" 
LABEL version="v1.0.0-slim"
LABEL maintainer="Paradoxis" 
LABEL website="https://github.com/Paradoxis/StegCracker/tree/v1.0.0"
LABEL license="MIT"

# Install dependencies
RUN apk update
RUN apk add steghide bash tar curl \
  --repository https://dl-3.alpinelinux.org/alpine/edge/testing

# Install StegCracker
RUN mkdir -p /usr/local/bin/
COPY ./stegcracker /usr/local/bin/stegcracker
RUN chmod +x /usr/local/bin/stegcracker

# Set data directory
VOLUME /data
WORKDIR /data

# Entrypoint
ENTRYPOINT ["/usr/local/bin/stegcracker"]
