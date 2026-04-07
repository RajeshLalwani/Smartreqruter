FROM golang:1.16-alpine
RUN adduser -D sandbox
USER sandbox
WORKDIR /home/sandbox
CMD ["go"]
