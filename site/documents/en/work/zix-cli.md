---
path: "/work/zix-cli"
title: "From an API specification to an explicit command."
summary: "A Rust dispatcher owns specification review and integrity checks; providers own transport and authentication. The released binary makes that boundary inspectable."
kind: "page"
status: "published"
---

## The dispatcher boundary

Separate specification input, explicitly selected operations, source hashes and provider execution contracts. The recorded run parses a synthetic OpenAPI document and extracts the GET /inspection route.

## Verification with a released binary

Run version, api project and api routes with v0.2.2 and retain actual inputs and outputs in examples/zix. The observation uses no credential, external request or live data mutation. Group-writable catalog input was refused as designed.

