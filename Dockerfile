FROM linaro/ci-amd64-llp-alpine

ADD . /srv/linaro-license-protection

#ADD secrets.py /srv/secrets.py
RUN echo "*" >> /srv/allowed_hosts.txt
ENV allowed_hosts="*"
ENV DJANGO_DEBUG="y"
RUN apk add musl-dev openldap-dev gcc
RUN pip install -r /srv/linaro-license-protection/requirements.txt
COPY linaro_ldap.py /srv/linaro-license-protection/license_protected_downloads/linaro_ldap.py
#RUN /srv/linaro-license-protection/manage.py migrate # Used to build the sqlite database. Temp fix as codebase needs to be updated to delete old DB calls

# README
# Mount a docker "bind" mount for on-the-fly reloading
#
# Run Django in debug mode a.k.a "runserver"
#
#
# docker run -it --mount src="$(pwd)",target=/srv/linaro-license-protection,type=bind -e DJANGO_DEBUG=Y -e DJANGO_MIGRATE=Y -e DJANGO_COLLECTSTATIC=Y -e DJANGO_SETTINGS_MODULE=settings -p 8080:8080 linaro/ci-amd64-llp-alpine
#
#
# Run in "production" mode
# Run docker in "S3" mode (settings.production) in django runserver
# Requires putting snapshots/releases.linaro.org into /etc/hosts and secrets.py being copied
#
# docker run -it --mount src="$(pwd)",target=/srv/linaro-license-protection,type=bind -e allowed_hosts=snapshots.linaro.org --mount src="$(pwd)/secrets.py",target=/srv/secrets.py,type=bind -p 8080:8080 linaro/ci-amd64-llp-alpine
#
