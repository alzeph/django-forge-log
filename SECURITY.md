# Security policy

*English | [Français](SECURITY.fr.md)*

## Reporting a vulnerability

Please do not open a public issue for a security flaw. Instead,
contact the maintainer directly at
[hervecedricyouan@gmail.com](mailto:hervecedricyouan@gmail.com) with:

- a description of the issue and its impact;
- reproduction steps;
- the affected `django-forge-log` version.

A response is targeted within 5 business days.

## Points of attention specific to an audit trail

`django-forge-log` potentially logs sensitive data (before/after
values of changed fields). Before reporting a PII leak as an
application bug, first check `FORGE_LOG["EXCLUDED_FIELDS"]` and
`FORGE_LOG["MASKED_FIELDS"]` — see the README, Security and PII
section. A misconfiguration on the user project's side is not a
vulnerability in the library, but any gap in the provided defaults
(common sensitive fields not covered) is one and should be reported.
