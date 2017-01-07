FROM quay.io/letsencrypt/letsencrypt:latest

MAINTAINER Gandi <https://github.com/Gandi/letsencrypt-gandi>

# Install sftp
RUN apt-get update && apt-get install -y openssh-client

# Copy plugin files
COPY letsencrypt_gandi	/opt/letsencrypt-gandi/letsencrypt_gandi
COPY setup.py 			/opt/letsencrypt-gandi/setup.py

# Register the plugin
RUN cd /opt/letsencrypt-gandi && /opt/certbot/venv/bin/pip install -e .

ENTRYPOINT [ "certbot" ]
