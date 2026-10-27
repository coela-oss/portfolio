# Contact form activation

The site consumes the published `@nuxtjp/contact-form` package. `contact-form.config.json` selects the same-origin API, registered site identity, reply-address mode and immutable policy version. No provider credential belongs in these files.

`mode: preview` does not submit messages. Keep it until the shared Rust receiver, allowed origins, Turnstile widget, mailbox-scoped Microsoft Graph application authorization, fixed recipient configuration and synthetic mailbox delivery have been verified. Use `mode: live` only with the real public widget key and matching receiver policy version. The public site package never contains the Turnstile secret.

The common policy is adopted at `urn:coela:legal:organization:hat-inc:privacy-policy@b282737cf7f67acc7a714f331c99d8b9b88992ce` and published centrally at https://hat-tech.co.jp/privacy. Reply email is optional for both pilots. IP/CIDR admission and site enable/disable controls belong to receiver configuration, not browser code.

The consent module controls only explicitly registered optional services. It cannot stop Cloudflare's automatic RUM insertion. Complete the separately approved provider configuration correction before treating automatic analytics as disabled. The English-default Coela site also requires the shared consent module's default-locale correction before production rollout.

Retain existing site deployment and public-file/DNS/binding verification. A local preview or successful provider send is not evidence that a mailbox received the message.

Delivery uses the shared contact Worker with Microsoft Graph, not Cloudflare Email Sending/Routing. Preserve the Microsoft 365 mail DNS. The sender is fixed by mailbox GUID, and optional visitor addresses are Reply-To only. Never place the application secret in public site configuration. The reviewed processor wording must match this delivery path before production policy publication.
