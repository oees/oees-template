# Troubleshooting a deploy: Django site

Start with the `deploy` workflow run in GitHub Actions: it prints the App Platform build and deploy logs. For more, run these **read-only** commands:

```bash
doctl apps list-deployments APP_ID              # ACTIVE or ERROR?
doctl apps logs APP_ID web --type build         # build failures
doctl apps logs APP_ID migrate --type deploy    # the PRE_DEPLOY migrate job
doctl apps logs APP_ID web --type run           # runtime errors
doctl apps spec get APP_ID                      # the live config
```

| Symptom | Likely cause | Fix |
|---|---|---|
| The first deploy fails at `migrate` with a connection timeout | The app is not in the cluster's Trusted Sources yet. Expected on the first deploy | Runbook step 3.4 (`firewalls append`, never `update`), then 3.5. |
| A timeout on a later deploy, or `/readyz` returns 503 | The firewall rule is gone, a URL is pasted instead of bound, or the regions differ | Use `${db.DATABASE_URL}` only. Keep `region: ams`. Check `doctl databases firewalls list CLUSTER_ID -o json`. |
| "database … does not exist" | The database was not created; the spec does not create it on this cluster | Runbook step 2.2. |
| "permission denied for schema public" | The app user cannot create tables | Runbook step 2.3. |
| The migrate job tries to create a user and fails | `db_user` is missing from the `databases:` block | Pin `db_user` to the site's own user. Never `doadmin`. |
| `/healthz` is 200 but pages return 500 | The tables do not exist: no `migrate` job, it failed, or a migration is not committed | Check the `migrate` deploy log. `make check` fails on a model change without a migration. |
| `deploy` fails with "`NAME` is referenced in the spec but not set" | A `${NAME}` in `.do/app.yaml` has no `env:` line in `deploy.yml`, or the secret is not in `production` | Add the `env:` line and the secret. Never remove the guard step. |
| 400 Bad Request on the custom domain | The hostname is not in `DJANGO_ALLOWED_HOSTS` | Keep `DJANGO_ALLOWED_HOSTS: ${APP_DOMAIN}` and make the domain `PRIMARY`. |
| "CSRF verification failed" on forms | The origin is not in `DJANGO_CSRF_TRUSTED_ORIGINS` | Keep `DJANGO_CSRF_TRUSTED_ORIGINS: ${APP_URL}`. |
| Pages show English instead of Spanish | The catalogues were not compiled, or a string has no translation | The image build compiles them. `make check` fails on untranslated entries. |
| A page loads a font, map or script but the browser blocks it | The origin is not in the Content Security Policy | Add the origin in `config/settings/csp.py` with a comment giving the reason. Review it like code. |
| Tests pass in CI, but SQL fails in production | The cluster runs another Postgres major than CI | Match the Postgres images in `compose.yml` and `ci.yml` to the cluster. |
| Config changed back after a deploy | Someone edited the app in the console. Each deploy applies the whole spec | Put the setting in `.do/app.yaml`, and secrets in `production`. |
| A secret is in a zip or in git | Committed or zipped by mistake | Rotate it now. If it reached git, scrub the history. |
