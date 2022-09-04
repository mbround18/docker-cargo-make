# docker-cargo-make

Dead simple image which houses [cargo-make]. Any and all issues involving [cargo-make] should be redirected to their repo. 
Any issues with this docker container should be logged here. 



[cargo-make]: https://github.com/sagiegurari/cargo-make


## Usage 

### Dockerfile

```Dockerfile
FROM rust:1.63 as builder
WORKDIR /data/odin
COPY . .
COPY --from=cargo-make /usr/local/bin/cargo-make /usr/local/cargo/bin
RUN /usr/local/cargo/bin/cargo make build
```

[**For an example of this in an existing project, click here**](https://github.com/mbround18/valheim-docker/blob/ab63fe348eb1b7425508b461e4835ca43676db2e/Dockerfile.odin#L32)

