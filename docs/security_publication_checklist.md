# Public Publication Checklist

Use this before making the repository public or sharing a documentation export.

## Keep Out Of Public Git

- Real personal or tenant mailbox addresses.
- Real hosted service URLs.
- Token cache filenames tied to a person.
- `.env` values, secrets, tokens, client secrets, refresh tokens, or auth cache files.
- Tenant-specific Power Automate run IDs, next-run timestamps, environment names, and secret-rotation notes.
- Mailbox-derived audit files or fixtures containing names, addresses, subjects, previews, bodies, or client/supplier names.
- Deployment-specific diagnostic output that exposes configured identities.

## Acceptable Public Examples

- `example.com` addresses.
- Placeholder service URLs such as `https://your-day-captain-service.example.com`.
- Required Graph scope names when documented as setup prerequisites.
- Aggregate-only audit statements with no real dates, recipients, subjects, bodies, addresses, tenant names, or exact production windows.

## Check

Run:

```sh
scripts/check_public_exposure.sh
```

If it reports matches, either anonymize the tracked file or move the deployment-specific detail to the private ops repository.
