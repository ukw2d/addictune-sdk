# Changelog

## 0.4.4

- Distinguish application authentication rejection from account credential failures: a `member_sessions` HTTP 401 Basic challenge now raises `AddictuneAppAuthError`, an `AddictuneAPIError` preserving `status_code == 401`.
- Keep ordinary 401/403 and invalid-credential 422 handling unchanged. The new exception uses a controlled message instead of the upstream response body.
- Add regression coverage for Basic challenges and misleading authentication parameters. The application identity remains in one `_APP_AUTH` constant for future rotation.

## 0.4.3

- Restore member-session login after AudioAddict stopped accepting the previous application HTTP Basic identity. Account credentials and the `member_sessions` request/response contract are unchanged.
- Add request-level authentication regression coverage for DI.FM, RadioTunes, ROCKRADIO, JAZZRADIO, Classical Radio and ZenRadio.
- Verify session creation on all six networks and an authenticated DI.FM member request.

The application identity is undocumented and may be revoked again. This patch does not change authentication error classification.
