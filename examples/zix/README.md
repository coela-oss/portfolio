# Recorded Zix CLI example

Observed on 2026-10-21 using the public zixcel/cli v0.2.2 binary.
The OpenAPI service is synthetic (`example.invalid`). These commands parse local
files and inspect routes; they make no API call and use no credential or provider.
The portfolio image is a formatted view of the recorded stdout, not an interactive
product console. The raw input, review, catalog and route output are retained here.

```sh
umask 077
zix --version
zix api project "$PWD/service.openapi.json" "$PWD/review.json" > catalog.json
zix api routes "$PWD/catalog.json" > routes.json
```

Use the named public release and verify its checksums before reproducing.
Zix refuses a group-writable catalog; retain restrictive local output permissions.
No installed provider, login or live cloud resource is needed for this example.
