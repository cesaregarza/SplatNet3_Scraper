# Upgrade to 2.0.0 (NXAPI-auth)

## What changed

- The default f-token provider now requires nxapi-auth client credentials to call the hosted f-generation API.
- The default scope is `ca:gf ca:er ca:dr`, matching the hosted nxapi examples and covering the optional encrypt/decrypt helpers.

## Action required

1. Create an nxapi-auth client (a public client is sufficient if the portal does not expose secrets).
2. Set the following environment variables for each worker/process:

   ```bash
   NXAPI_ZNCA_API_CLIENT_ID=...                  # required
   # choose ONE
   NXAPI_ZNCA_API_CLIENT_SECRET=...              # or
   NXAPI_ZNCA_API_CLIENT_ASSERTION=...           # + NXAPI_ZNCA_API_CLIENT_ASSERTION_TYPE=...
   # or generate private_key_jwt from your registered JWKS metadata
   NXAPI_ZNCA_API_CLIENT_ASSERTION_PRIVATE_KEY_PATH=/path/to/private.pem
   NXAPI_ZNCA_API_CLIENT_ASSERTION_JKU=https://example.com/.well-known/jwks.json
   NXAPI_ZNCA_API_CLIENT_ASSERTION_KID=my-key-id
   NXAPI_ZNCA_API_AUTH_SCOPE="ca:gf ca:er ca:dr"
   NXAPI_USER_AGENT="my-scraper/2.0.0 (+https://example.com/contact)"
   ```

3. If you build from source or embed the library, call `setClientAuthentication({ id, scope: 'ca:gf ca:er ca:dr', ... })` before making requests.

## Notes

- The config loader still accepts `nxapi_shared_secret` when reading older config files, but `nxapi_client_secret` is the canonical key to write going forward.
- The hosted f-generation service has required client authentication since June 2025.
- If you use the hosted service, disclose that a Nintendo `id_token` is sent to a third party and link the Public API terms and status page.

## References

- nxapi README (environment variables, user-agent requirements, code examples).
- nxapi-znca-api README (public API terms, status page).
- nxapi-auth README (supported client authentication methods).
