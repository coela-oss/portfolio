# Engineering principles

I use these principles to explain and review engineering choices. They are
Coela's guidance, not universal rules or permission to operate a system.

## Keep data under its owner's control

I prefer local-first data and explicit synchronization. Storage ownership,
backup, recovery and export should remain understandable without a mandatory
cloud relay.

## Give each component one responsibility

I separate business data, language meaning, communication, credential custody
and execution policy. Shared libraries should implement common contracts;
product integrations should contain only their own decisions and mappings.

## Make authority explicit

A useful recommendation does not authorize an action. Reading a document,
receiving a package, trusting its publisher, installing it and executing an
operation require distinct decisions and evidence.

## Preserve evidence and uncertainty

I distinguish implementation, development tests, package publication,
deployment and actual use. Missing or partial evidence remains visible rather
than becoming a successful result.

## Prefer maintainable implementations

I use Rust for core behavior and strict TypeScript for UI and integration where
they fit. I prefer small components, clear names and published dependencies
over duplicated frameworks or compatibility maintained without a current need.
