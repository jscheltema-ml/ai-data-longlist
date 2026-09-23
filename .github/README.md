# CI/CD

One workflow (`workflows/ci-cd.yml`) orchestrates everything:

```
changes  → detect which components changed (git diff)
build    → _build.yml   (PR: lint / validate-build / terraform plan;
                         push: build + push image)
deploy   → _deploy.yml  (push to development or dispatch: terraform apply,
                         roll the backend by digest)
```

**Components** (each built/deployed only when it changed — see `actions/detect-changes`):
`backend` = `src/core` · `infra` = `infra-longlist`.

**Branch model** (dev only for now):

| event | CI (build/plan) | deploy |
|---|---|---|
| PR → `development` / `main` | ✅ | ❌ |
| push → `development` | ✅ | ✅ dev |
| push → `main` | ✅ | ❌ (CI-only; prd not bootstrapped) |
| manual dispatch | ✅ | ✅ dev |

**Design notes**
- Build once, deploy by digest (`actions/build-image` → `actions/deploy-image`), so dev and prd get byte-identical images.
- Config lives in `config/<env>.json`, parsed by `actions/load-config`. Non-secret IDs (`azure_client_id`, `gh_app_id`, `app_client_id`, tenant/subscription) are in config; only `AZURE_CLIENT_SECRET_<ENV>` and `GH_APP_PRIVATE_KEY` are GitHub secrets.

---
### prd (later)
- [ ] Bootstrap prd: create the prd Entra app registration → set `config/prd.json` `app_client_id`; add the `*_PRD` secrets; add a `main` → prd deploy path; run the first apply, then it's self-maintaining.
