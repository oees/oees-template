# Troubleshooting a deploy: Django site

Start with the app's **Activity** tab in the DigitalOcean console: it lists each deployment with its logs. For more, run these **read-only** commands:

```bash
doctl apps list-deployments APP_ID              # ACTIVE or ERROR?
doctl apps logs APP_ID web --type build         # build failures
doctl apps logs APP_ID migrate --type deploy    # the PRE_DEPLOY migrate job
doctl apps logs APP_ID web --type run           # runtime errors
doctl apps spec get APP_ID                      # the live config
```

| Symptom | Likely cause | Fix |
|---|---|---|
| The first deploy fails at `migrate` with a connection timeout | The app is not in the cluster's Trusted Sources yet. Expected on the first deploy | Runbook step 3.5 (`firewalls append`, never `update`), then 3.7. |
| A timeout on a later deploy, or `/readyz` returns 503 | The firewall rule is gone, a URL is pasted instead of bound, or the regions differ | Use `${db.DATABASE_URL}` only. Keep `region: ams`. Check `doctl databases firewalls list CLUSTER_ID -o json`. |
| "database … does not exist" | The database was not created; the spec does not create it on this cluster | Runbook step 2.2. |
| "permission denied for schema public" | The app user cannot create tables | Runbook step 2.3. |
| The migrate job tries to create a user and fails | `db_user` is missing from the `databases:` block | Pin `db_user` to the site's own user. Never `doadmin`. |
| `/healthz` is 200 but pages return 500 | The tables do not exist: no `migrate` job, it failed, or a migration is not committed | Check the `migrate` deploy log. `make check` fails on a model change without a migration. |
| The app does not start, and the log says that `SECRET_KEY` is empty | The secret has no value in App Platform, or someone applied `.do/app.yaml` itself and removed it | Set it in the console (runbook step 3.6). Apply spec changes only from the live spec (runbook section 4). |
| A merge did not deploy | `deploy_on_push` is off in the live spec, or the DigitalOcean GitHub app cannot read the repository | Check `doctl apps spec get APP_ID` and the repository access of the GitHub app. |
| 400 Bad Request on the custom domain | The hostname is not in `DJANGO_ALLOWED_HOSTS` | Keep `DJANGO_ALLOWED_HOSTS: ${APP_DOMAIN}` and make the domain `PRIMARY`. |
| "CSRF verification failed" on forms | The origin is not in `DJANGO_CSRF_TRUSTED_ORIGINS` | Keep `DJANGO_CSRF_TRUSTED_ORIGINS: ${APP_URL}`. |
| Pages show English instead of Spanish | The catalogues were not compiled, or a string has no translation | The image build compiles them. `make check` fails on untranslated entries. |
| A page loads a font, map or script but the browser blocks it | The origin is not in the Content Security Policy | Add the origin in `config/settings/csp.py` with a comment giving the reason. Review it like code. |
| Tests pass in CI, but SQL fails in production | The cluster runs another Postgres major than CI | Match the Postgres images in `compose.yml` and `ci.yml` to the cluster. |
| `.do/app.yaml` and the live app differ | Someone changed the app in the console, or nobody applied a merged spec change | Compare `doctl apps spec get APP_ID` with `.do/app.yaml`. Fix the file in a pull request, then apply it (runbook section 4). |
| A secret is in a zip or in git | Committed or zipped by mistake | Rotate it now. If it reached git, scrub the history. |
