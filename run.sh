#!/bin/bash

docker run -it --name linaro --mount src="$(pwd)",target=/srv/linaro-license-protection,type=bind -e DJANGO_DEBUG=Y -e DJANGO_MIGRATE=Y -e DJANGO_COLLECTSTATIC=Y -e DJANGO_SETTINGS_MODULE=settings -p 8080:8080 seojikim/ci-amd64-llp-alpine
