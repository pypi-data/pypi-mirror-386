.PHONY: help docker-build
.DEFAULT: help

tag="nibabies"

help:
	@echo "Premade recipes"
	@echo
	@echo "make docker-build [tag=TAG]"
	@echo "\tBuilds a docker image from source. Defaults to 'nibabies' tag."


docker-build:
	docker build --rm -t $(tag) \
	--build-arg BUILD_DATE=`date -u +"%Y-%m-%dT%H:%M:%SZ"` \
	--build-arg VCS_REF=`git rev-parse --short HEAD` \
	--build-arg VERSION=`python -m hatch version` .
