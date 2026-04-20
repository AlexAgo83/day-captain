# Changelog (`1.9.3 -> 1.9.4`)

## Major Highlights

- Hardened Microsoft Graph reads in the digest flow so transient `504 Gateway Timeout` responses retry instead of failing the hosted job immediately.
- Kept the retry logic bounded to read operations to avoid duplicate side effects on Graph write requests.

## Version 1.9.4

### Delivered

- Added bounded retry handling to `GraphApiClient.get_object` for transient Graph failures including `429`, `500`, `502`, `503`, and `504`.
- Split Graph GET handling into a retryable inner request path while leaving POST delivery logic unchanged.
- Added regression coverage for successful retry recovery and non-retryable Graph error behavior.

### Validation

- `python3 -m unittest tests.test_graph_client`
- `python3 -m pytest -q`
