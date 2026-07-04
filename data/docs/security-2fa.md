---
doc_id: security-2fa
title: Setting Up Two-Factor Authentication
category: security
---

# Setting Up Two-Factor Authentication

## Enabling 2FA

Go to Settings > Security > Two-Factor Authentication > Enable. Scan the QR
code with an authenticator app (Google Authenticator, Authy, 1Password, etc.)
and enter the 6-digit code to confirm.

## Backup codes

After enabling 2FA, Cloudbox shows 10 one-time backup codes. Save these
somewhere safe — each can be used once to sign in if you lose access to your
authenticator app. You can regenerate a new set from Settings > Security at
any time, which invalidates the old codes.

## Losing access to your authenticator

If you lose your device and don't have backup codes, account recovery
requires identity verification by our security team (government ID plus a
recent invoice), since we can't safely disable 2FA on a support agent's say-so
alone. This process typically takes 1–3 business days.

## Disabling 2FA

Settings > Security > Two-Factor Authentication > Disable, confirmed with a
current code or backup code. We recommend keeping 2FA enabled, especially if
you store sensitive files.

## SMS-based 2FA

Cloudbox does not support SMS-based 2FA; only authenticator apps (TOTP) and
backup codes are supported, because SMS is vulnerable to SIM-swapping
attacks.
