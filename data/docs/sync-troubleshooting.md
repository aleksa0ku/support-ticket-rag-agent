---
doc_id: sync-troubleshooting
title: Troubleshooting Files That Won't Sync
category: sync
---

# Troubleshooting Files That Won't Sync

## Check sync status first

Click the Cloudbox tray/menu-bar icon to see overall status. Common states:

- **Syncing** — normal, wait for it to finish.
- **Paused** — sync was manually paused, or paused due to low disk space or
  battery saver mode.
- **Error** — one or more files failed; click "View issues" for details.

## Common causes and fixes

- **File name issues**: Characters like `\ / : * ? " < > |` aren't allowed on
  Windows and will block sync. Rename the file to remove them.
- **File too large**: Individual files over 50 GB (Plus/Family) or 200 GB
  (Business) aren't supported. Split large files or use archive/compression.
- **Path too long**: Windows has a 260-character path limit. Move the file to
  a shallower folder or shorten folder names.
- **Antivirus/firewall interference**: Some antivirus tools quarantine the
  sync client's temp files. Add the Cloudbox folder and app to your
  antivirus exclusion list.
- **Out of local disk space**: Cloudbox needs free space to stage downloads.
  Free up space or enable "online-only files" mode in Settings > Sync.

## Forcing a resync

Settings > Sync > Advanced > "Rebuild sync database" clears the local sync
index and re-scans everything. This is safe — it doesn't delete files — but
can take a long time for large accounts.

## Still stuck?

If a specific file consistently fails after trying the above, gather the
error message from "View issues" and file a ticket — some failures require
looking at server-side sync logs.
