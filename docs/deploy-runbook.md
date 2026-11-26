# Deploy runbook: Django site

For the OEES tech team. The marketing owner sends a zip that `make package` built. You import it into a repository, prepare the database, review, and merge. **The merge is the deploy, and not merging is the veto.**

Each command says if it is **READ-ONLY** or if it **CHANGES** something.

## How the deploy works

- One App Platform app per site, named `<site>-prod`, in region `ams`.
- App Platform deploys every push to `main` by itself (`deploy_on_push: true`), through the DigitalOcean GitHub app. There is no deploy workflow in `.github/`.
- `main` changes only through a pull request. The protection of `main` (step 1.1) is the only gate before production. A pull request runs `ci`: `check` (`make check` against Postgres 18), `secrets` (gitleaks) and `image` (Docker build and a `/healthz` smoke test).
- The `migrate` `PRE_DEPLOY` job runs `python manage.py migrate --noinput` before each rollout.
- App Platform keeps its own copy of the app spec. You create the app from `.do/app.yaml` once (section 3). A later change to `.do/app.yaml` reaches the app only when you apply it (section 4).
- Secrets have no value in `.do/app.yaml`. You set each one in the App Platform console, encrypted. The live spec holds them as encrypted values (`EV[…]`).
- Never change the app only in the console, except secret values. Put the change in `.do/app.yaml` in a pull request, then apply it.
- The database is on the cluster `oees-tech-template-repo-ddbb`. Every site made from this template has its own database and its own user on it. App Platform did not create the cluster, so attaching it in the spec does **not** create the database, the user or the firewall rule. You do those by hand (section 2).

The template has no Celery worker and no Redis. Add them only when a site needs background jobs, and provision Valkey for them.

## 1. Import the zip

1. **CHANGES** — Create `oees/<site>` from this template (**Use this template** on GitHub). Allow rebase merging only. Protect `main` with a ruleset or a branch protection rule:
   - Require a pull request with one approval.
   - Require the `ci` checks `check`, `secrets` and `image`, and require the branch to be up to date before the merge.
   - Block force pushes and deletions.
   - Allow nobody to bypass the rule, admins included: every push to `main` deploys.
2. **CHANGES** — Import the zip on a branch, so that the pull request shows only the owner's work against the template:

   ```bash
   unzip <site>-<stamp>.zip -d /tmp/import
   git clone git@github.com:oees/<site>.git && cd <site>
   git switch -c import/<yyyy-mm-dd>
   rsync -a --delete --exclude .git /tmp/import/<site>/ ./
   git add -A && git commit -m "Import <site> from marketing"
   git push -u origin HEAD
   ```

   Open a pull request into `main`.
3. **READ-ONLY** — Review:
   - `HANDOFF.md`: every item under **For review**, **Data the site stores**, **Migrations** and **Secrets needed**.
   - Every migration. Each one must work with the code that is already running.
   - The diff of `.do/`, `.github/`, `Dockerfile`, `compose.yml`, `Makefile`, `make/`, `config/settings/`, `pyproject.toml` and `scripts/`. A new workflow that deploys is a reason to veto.
   - The `ci` result.
   - The agent configuration: `uvx --from git+https://github.com/oees/agents@v1.0.0 oees-agents check`. It fails if someone edited the generated rules.
4. **CHANGES** — Fix what the owner could not know, on the same branch:
   - In `.do/app.yaml`: `name: <site>-prod`, both `github.repo: oees/<site>`, and `db_name` and `db_user` (the slug with underscores). Keep `version: "18"`: it is the major version of the cluster. If the cluster moves to another major, change `version` and the Postgres images in `compose.yml` and `.github/workflows/ci.yml` together, pinned by digest.
   - In `.oees-agents.toml`: the `[project]` name and description. Then run `uvx --from git+https://github.com/oees/agents@v1.0.0 oees-agents update` and commit the result.
5. **CHANGES** — Once per repository: give the DigitalOcean GitHub app access to `oees/<site>`.

## 2. Prepare the database (before the first deploy)

1. **READ-ONLY** — Get the cluster ID, region and version. The region must be `ams`, and the major version must be the `version` in the spec (18).

   ```bash
   doctl databases list
   doctl databases get CLUSTER_ID --format ID,Name,Engine,Version,Region
   ```

2. **CHANGES** — Create the site's database and its own user, with the `db_name` and `db_user` from `.do/app.yaml` (the site slug with underscores, for example `campaign_2027`). Do not record the password: App Platform reads it through the `${db.DATABASE_URL}` binding.

   ```bash
   doctl databases db create CLUSTER_ID <db_name>
   doctl databases user create CLUSTER_ID <db_user>
   ```

3. **CHANGES** — Let the user create tables in its own database. Connect as `doadmin` to the database `<db_name>`. If the cluster already has a per-app pattern, use it instead.

   ```sql
   GRANT USAGE, CREATE ON SCHEMA public TO <db_user>;
   -- Optional: only this app's user can connect to this database.
   -- REVOKE CONNECT ON DATABASE <db_name> FROM PUBLIC;
   -- GRANT CONNECT ON DATABASE <db_name> TO <db_user>;
   ```

   Never use `doadmin` as the app's `db_user`. It is the cluster superuser and reaches the data of every site on the cluster.

## 3. First deploy

1. **READ-ONLY** — `doctl apps spec validate .do/app.yaml`
2. **CHANGES** — Merge. No app exists yet, so nothing deploys.
3. **CHANGES** — Create the app from `main`:

   ```bash
   git switch main && git pull
   doctl apps create --spec .do/app.yaml
   ```

   This first deployment **fails**, and that is expected: `DJANGO_SECRET_KEY` has no value yet, and the app is not in the cluster firewall.
4. **READ-ONLY** — Get the app ID: `doctl apps list --format ID,Spec.Name,DefaultIngress`
5. **CHANGES** — Add the app to the cluster's Trusted Sources. Use `append`. **Never use `firewalls update`**: it replaces every rule and cuts off the other sites on the cluster.

   ```bash
   doctl databases firewalls append CLUSTER_ID --rule app:APP_ID
   ```

6. **CHANGES** — Set the secrets in the DigitalOcean console: open the app, then **Settings**, then **App-Level Environment Variables**, then **Edit**. For each secret, paste the value, tick **Encrypt**, and save. Saving starts a new deployment.

   | Secret | Value |
   |---|---|
   | `DJANGO_SECRET_KEY` | `python3 -c "import secrets; print(secrets.token_urlsafe(50))"` |
   | Each name under **Secrets needed** in `HANDOFF.md` | As the hand-off says. Keep the value only in the password manager and in App Platform |

7. **CHANGES** — If no deployment started, start one: `doctl apps create-deployment APP_ID`. From now on, each merge deploys.
8. **READ-ONLY** — Verify:

   ```bash
   doctl apps list-deployments APP_ID                 # the latest deployment is ACTIVE
   doctl databases firewalls list CLUSTER_ID -o json  # the app is present
   doctl databases db list CLUSTER_ID                 # <db_name> is present
   ```

   `doctl databases firewalls list` does not accept `--no-header`. With it, the command errors, and a `grep` over the error reports a false "not found".

9. **READ-ONLY** — Smoke test: `/healthz` and `/readyz` return 200, the home page, an unknown path (the site's 404 page), one page that reads from the database, and one form submission with synthetic data. For a staff-only site, an anonymous visitor gets the login page.
10. **CHANGES** — If the owner reads the stored data in `/admin/`, give them an account:
    1. Run `doctl apps console APP_ID web`, then `python manage.py createsuperuser` for yourself.
    2. In `/admin/`, create a staff account for each person that `HANDOFF.md` names. Give it only the view permission on the site's models.
    3. Send each password through the password manager, never in chat or email.
11. **CHANGES** — If `HANDOFF.md` says the site is staff-only, decide how staff log in: a Django account for each person (not staff, no admin access), or the company login. Then create the accounts, or connect the company login in a pull request.

To veto at any point, request changes or close the pull request, and tell the owner what to change.

## 4. Change the app configuration

A merged change to `.do/app.yaml` does not change the app by itself. Apply it after the merge. Start from the live spec, because only the live spec holds the secrets:

1. **READ-ONLY** — `doctl apps spec get APP_ID > /tmp/<site>-live.yaml`. In it, each secret has an encrypted value (`EV[…]`).
2. In `/tmp/<site>-live.yaml`, make the change that the pull request made to `.do/app.yaml`, and nothing else. Keep every `EV[…]` value as it is. A new secret gets its key and `type: SECRET`, with no value.
3. **READ-ONLY** — `diff /tmp/<site>-live.yaml .do/app.yaml`. Only the secret values, and fields that App Platform adds by itself, may differ. Anything else came from the console: bring it into `.do/app.yaml` in a pull request.
4. **READ-ONLY** — `doctl apps spec validate /tmp/<site>-live.yaml`
5. **CHANGES** — `doctl apps update APP_ID --spec /tmp/<site>-live.yaml`. This replaces the whole configuration of the app, and deploys it. Never apply `.do/app.yaml` itself to an existing app: it has no secret values, so the update would remove them.
6. **CHANGES** — For a new secret, set its value in the console as in step 3.6. Then remove `/tmp/<site>-live.yaml`.

## 5. A domain

1. Agree the hostname with the owner.
2. **CHANGES** — Add the `domains:` block (`type: PRIMARY`) to `.do/app.yaml` in a pull request. After the merge, apply it as in section 4. `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` follow the primary domain through `${APP_DOMAIN}` and `${APP_URL}`.
3. **CHANGES** — Point DNS at the app as App Platform shows for the domain. Wait for the certificate.

## 6. Later rounds

The owner continues from the last zip that they have, not from `main`. So the changes that you make on `main` are not in their copy.

- After each merge, send the owner a zip of `main` to continue from:

  ```bash
  git archive --format=zip --prefix=<site>/ -o <site>-main.zip main
  ```

- Import each new zip as in step 1.2, on a new branch from `main`. In the review, look for lines that the import removes. An import from an old copy undoes your changes, for example the database settings in `.do/app.yaml`.
