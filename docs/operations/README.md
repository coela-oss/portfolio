# Production verification

`current-production-verification.json` records the latest actual operator check,
including its context and the reviewed source/archive identity. The public
response report stays local; its SHA256 is recorded for audit. Use the owner
observation commands in the repository README to reproduce the public check.

For 0.1.9, local observation verified all 103 public assets, 44 redirects and
40 sitemap entries. The authenticated DNS/domain snapshots from immediately
before the initial deployment and the subsequent verify-only attempt agree.
The verify-only attempt did not deploy again.

The hosted probe encountered Cloudflare challenge pages with HTTP 403 on 86 of
103 requests. It remains blocked; this is not a successful hosted verification.
The observations do not identify which particular Cloudflare rule caused the
challenge. Cloudflare defense settings and release acceptance were not relaxed.

Investigate observer reports before retrying a production job. A public probe
failure does not establish that deployment failed and is not a reason to resend
an unknown write. Deployment and observation evidence retain separate meanings.
