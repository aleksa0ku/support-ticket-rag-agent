---
doc_id: integrations-api
title: API Access and Third-Party Integrations
category: integrations
---

# API Access and Third-Party Integrations

## Generating an API token

Business plan accounts can generate API tokens from Settings > Developer >
API Tokens. Tokens are scoped to read-only or read-write and can be revoked
individually at any time.

## Rate limits

The API allows 1,000 requests per hour per token on Business plans. The
response includes `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers so
you can back off before hitting the limit. Sustained rate-limit violations
may result in a temporary token suspension.

## Available integrations

Cloudbox has pre-built integrations with Zapier, Slack (file sharing to
channels), and Google Workspace (opening/editing Docs-format files directly
from Cloudbox). These are enabled per-user from Settings > Integrations.

## Webhooks

Business plan accounts can register webhook URLs (Settings > Developer >
Webhooks) to receive events for file uploads, deletes, and share-link
creation. Webhook payloads are signed with an HMAC-SHA256 signature using
your webhook secret, which you should verify on receipt.

## Building a custom integration

Full API reference and authentication (OAuth2) documentation is published
separately for developers. General account-specific integration debugging
(e.g., a webhook silently failing for one particular account) typically
needs a support engineer to check server-side delivery logs.
