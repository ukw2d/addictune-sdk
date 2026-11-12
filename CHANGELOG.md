# Changelog

## 0.4.3

- Restore member-session login after AudioAddict stopped accepting the previous application HTTP Basic identity. Account credentials and the `member_sessions` request/response contract are unchanged.
- Add request-level authentication regression coverage for DI.FM, RadioTunes, ROCKRADIO, JAZZRADIO, Classical Radio and ZenRadio.
- Verify session creation on all six networks and an authenticated DI.FM member request.

The application identity is undocumented and may be revoked again. This patch does not change authentication error classification.
