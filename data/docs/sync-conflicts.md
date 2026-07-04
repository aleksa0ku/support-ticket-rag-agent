---
doc_id: sync-conflicts
title: Understanding Conflicted Copies
category: sync
---

# Understanding Conflicted Copies

## Why conflicted copies happen

When the same file is edited on two devices while one was offline, Cloudbox
can't automatically merge the changes. Instead it keeps both versions: the
original file keeps syncing normally, and the other edit is saved alongside
it as `filename (Conflicted copy YYYY-MM-DD).ext`.

## Resolving a conflict

1. Open both versions and compare them.
2. Keep the one you want under the original filename; you can merge changes
   manually if both have edits you need.
3. Delete the conflicted copy once you've resolved it, or keep it as a
   backup — it doesn't affect sync either way.

## Reducing conflicts

- Avoid editing the same file offline on multiple devices at once.
- For documents multiple people edit together, consider a format with
  real-time co-editing instead of syncing a single file.
- Keep devices online and synced regularly rather than working offline for
  long stretches.

## Conflicts in shared folders

In [shared folders](sharing-teams), conflicts can also happen when two
different people edit the same file at the same time. The same
conflicted-copy naming applies, tagged with the device name that created it.
