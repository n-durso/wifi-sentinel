FROM ubuntu:latest
LABEL authors="marcomaraglino"

ENTRYPOINT ["top", "-b"]