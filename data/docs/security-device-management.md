---
doc_id: security-device-management
title: Managing Linked Devices and Sessions
category: security
---

# Managing Linked Devices and Sessions

## Viewing linked devices

Settings > Security > Devices lists every device currently signed in,
including device name, OS, approximate location (based on IP), and last
active time.

## Revoking a device

Click "Revoke" next to any device to sign it out immediately. The Cloudbox
app on that device stops syncing and requires signing in again — files
already downloaded to that device are not deleted, only future sync access
is cut off.

## "I don't recognize this device"

If you see a device you don't recognize, revoke it immediately and change
your password from Settings > Security > Password. We also recommend
enabling [two-factor authentication](security-2fa) if it isn't already on.
If you believe your account was accessed by someone else and files may have
been viewed, downloaded, or deleted without your permission, this is a
security incident and should be escalated to our security team directly
rather than handled as a routine ticket.

## Session length

Desktop and mobile app sessions stay signed in until manually revoked or the
password is changed (which revokes all sessions except the current one).
Web sessions expire after 30 days of inactivity.
