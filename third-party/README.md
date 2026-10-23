# Source-controlled dependency patches

The patches in the adjacent `patches/` directory retain upstream source context.
Original copyright and complete license texts are included here:

| Dependency | Copyright | Selected license |
| --- | --- | --- |
| braces 3.0.3 | 2014-present, Jon Schlinkert | [MIT](LICENSES/braces-3.0.3.txt) |
| node-forge 1.4.0 | 2010, Digital Bazaar, Inc. | [BSD-3-Clause option](LICENSES/node-forge-1.4.0.txt) |

The node-forge file retains its complete original dual-license text. These
notices do not change the application's own license or replace other dependencies'
notices. Include them when distributing the checked-in patches.

[Source provenance](patch-attribution.json) records official npm tarball integrity,
original license and modified-file hashes, and the local patch hashes. Null marks
a locally added file. Braces changes bound tree depth and reject cycles; node-forge
changes reject malformed RSA algorithm parameters. The recorded review date is
an actual source comparison, not an automatically refreshed freshness claim.
Changes require renewed source/license comparison and the existing regression tests.
This covers the source-controlled patches, not a complete distribution SBOM.

## Engineering guidance snapshot

`engineering/` is an exact selected source snapshot from coela-oss/engineering,
recorded with immutable source commit and per-file SHA256 in `provenance.json`.
Original reader code is MIT; original prose/catalog is CC BY 4.0. Its LICENSE and
both license texts are retained. The displayed excerpts credit Coela and link to
exact original language/source and CC BY 4.0. Whitespace is normalized and excerpts
are bounded by the upstream projection, with no separate editorial rewrite.

Update using `node scripts/update-engineering.mts /reviewed/engineering/checkout
FULL_COMMIT_SHA`. The command requires the exact clean source commit, copies only
the selected tracked files, and executes that admitted owner's existing projection.
`site/guidance.json` is generated and checked against the pinned source on tests
and before each Nuxt build. Do not edit the snapshot or generated excerpts by hand.
The build has no network dependency on GitHub or an engineering service.
