# Public Release Checklist

Run this checklist before making Buddy-Agent public. Do not make the repository public until every blocker is resolved.

## Local quality gates

```bash
ruff check .
mypy src
pytest
buddy doctor
buddy smoke
buddy alpha
buddy parity
buddy skills validate
```

## Secret scans

Run against the current tree:

```bash
gitleaks detect --source . --verbose
trufflehog git file://. --only-verified
```

Run against full history:

```bash
gitleaks detect --source . --log-opts="--all" --verbose
```

Do not claim these scans passed unless they were actually run and reviewed.

## Manual review

- [ ] Review `LICENSE_MATRIX.md`.
- [ ] Review `THIRD_PARTY_NOTICES.md`.
- [ ] Confirm no private local paths.
- [ ] Confirm no secrets, API keys, tokens, cookies, passwords, OAuth secrets, account IDs, or private keys.
- [ ] Confirm no signed-in Safari automation or browser session automation is enabled by default.
- [ ] Confirm no live social/account automation is enabled by default.
- [ ] Confirm no gambling, trading, prediction-market, wallet-signing, deposit, withdrawal, or other money/regulatory execution skills are present in public defaults.
- [ ] Confirm risky skills are disabled, absent from `skills/public`, or documented as future work.
- [ ] Confirm Buddy-Agent public/private language is accurate.
- [ ] Confirm README says `runnable alpha`, not finished autonomous production operator.
- [ ] Confirm private repository links are not presented as public release links until the repo is actually public.
