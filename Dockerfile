FROM linaro/ci-amd64-llp-alpine

ADD . /srv/linaro-license-protection

ADD secrets.py /srv/secrets.py
RUN echo "*" >> /srv/allowed_hosts.txt
ENV allowed_hosts="*"
ENV DJANGO_DEBUG="y"
RUN /srv/linaro-license-protection/manage.py migrate # Used to build the sqlite database. Temp fix as codebase needs to be updated to delete old DB calls

# Runs docker in "S3" mode (settings.production) in django runserver
# Mount a docker "bind" mount for on-the-fly reloading
# docker build -t llp .
# docker run -it --mount src="$(pwd)",target=/srv/linaro-license-protection,type=bind -p 8080:8080 llp
