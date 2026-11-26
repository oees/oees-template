# Hand-off to OEES tech

> **Agent:** keep this file current while you work, in English. The OEES tech team reads it first when the zip arrives, and decides from it what to review before they deploy. Replace every `<…>`. Do not delete sections; write "None" where nothing applies.

## The site

| Item | Value |
|---|---|
| Name | `<site>` (the same as `name` in `pyproject.toml`; lowercase, hyphens) |
| What it is for | <one or two sentences> |
| Who can see it | <"anyone", or "OEES staff only: a login on every page"> |
| Owner in marketing | <name> |
| Public address wanted | <hostname, or "not decided"> |
| Launch date wanted | <date, or "not decided"> |
| Template | `oees-template` <version from TEMPLATE_VERSION> |

## Pages

| Path | What it shows | Reads or writes the database |
|---|---|---|
| `/` | <…> | <no> |

## Data the site stores

For each model: what it holds, which fields are personal data, who reads it in `/admin/`, the retention period and how a record gets deleted (the erasure path).

<"None.">

## Personal data

<"None: the site stores no data about visitors." Or: the fields, the purpose, where the data goes after the site, the retention period, and if the data protection officer (dpd@octopusenergy.es) was informed.>

## Migrations

Every migration in this zip that is not in the template, with one line on what it does. Flag any that drops, renames or rewrites data.

<"None.">

## Secrets needed

Every entry with `type: SECRET` in `.do/app.yaml` other than `DJANGO_SECRET_KEY`, with what it is and where its value comes from. Tech sets each value in App Platform. Never write a secret value here or in any file.

<"None.">

## Outside services

Every service the site loads or calls: fonts, analytics, tag managers, maps, video embeds, APIs, email. For each one: what it receives from the visitor, if it waits for cookie consent, and each origin added to `config/settings/csp.py`.

<"None.">

## For review

Decisions that tech should check before the deploy. List each one with the reason:

- anything outside the template's stack (a new framework, a library, a service, background jobs);
- every change to `.do/app.yaml`, `.github/`, `Dockerfile`, `compose.yml`, `Makefile`, `make/`, `config/settings/` or `scripts/`;
- every new dependency in `pyproject.toml`;
- prices, tariffs or savings figures on a page, and where they come from;
- legal text that still needs approval (privacy policy, cookie notice, consent text, conditions);
- files larger than 5 MB.

<"None.">

## Checks

Run on <date>, in <where: for example "the Claude chat workspace, Postgres 18 started locally">.

| Check | Result | Notes |
|---|---|---|
| `make check-fast` | <passed / failed / blocked> | <…> |
| `make check` | <passed / failed / blocked> | <…> |

A blocked check is not a pass. Say what blocked it.
