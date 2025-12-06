# Backups, UUIDs, and What JFIN Does (and Does Not) Back Up

Let me state this again clearly: **This. Is. Not. A. Backup. And. Restore. System!**  
JFIN includes a “backup” and “restore” function…  
but, again, these are **not real backups** in the Jellyfin sense.

Let’s be extremely clear:

## What JFIN does *not* back up

JFIN does not back up:

- Jellyfin's database  
- Item UUID mappings  
- Watch history  
- Playlists  
- Subtitles  
- Chapters or trickplay images  
- Anything outside the specific images JFIN touched  

## What JFIN *does* back up

Only the image files JFIN processed — nothing more, nothing less.

This lets you selectively restore:

- A single image  
- Logos only  
- Thumbs only  
- Specific libraries  

## Do NOT use JFIN to restore images after a full Jellyfin rebuild

If Jellyfin re-imports your media, **UUIDs will change**, and *JFIN cannot restore images to items that no longer exist under the same ID.*

The only exception:

- You restore a **Docker persistent volume** *unchanged*,  
- And, in this process, Jellyfin does **not** import the library again with a re-scan,  
- And all UUIDs remain identical to before restore.  

## Use Jellyfin’s built-in backup system for real backups

Jellyfin 10.11+ provides a robust, official, database-aware backup + restore.  
Use *that* for real server recovery, and treat JFIN’s backups as a convenience utility only.

This also means that any scripts that offer "backup and restore" such as [Jellyfin-Backup-Restore](https://github.com/laughingman77/Jellyfin-Backup-Restore) and [jellyfin-backup-script](https://github.com/Josh2kk/jellyfin-backup-script) are not guaranteed to work. These fail because they do not preserve or restore item UUIDs correctly, especially after reinstalling Jellyfin.

**Bottom line:**  
JFIN offers convenience restores - not disaster recovery.  
Always back up Jellyfin properly.
