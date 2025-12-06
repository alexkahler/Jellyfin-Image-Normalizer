# Advanced Usage & Tips

This page collects small but useful patterns and best practices that don’t fit in the basic README examples.

---

## Force-register a manually replaced image

If you manually replace an image inside your Jellyfin metadata folder and Jellyfin refuses to acknowledge it (cache might not be updated or old image size is still being shown in UI), you can force JFIN to re-upload the file:

```bash
python jfin.py --single <item_uuid> \
  --force-upload-noscale \
  --width <image_width> \
  --height <image_height>
````

This forces Jellyfin to associate the new file with the item, even if the dimensions didn’t change.

---

## Use a dedicated operator/admin user for JFIN

JFIN works best when you use a Jellyfin user with:

* Access to **all** libraries
* No parental controls
* No tag restrictions
* No watched-state tracking you care about

**Recommended pattern:**

1. Create a **“maintenance admin”** account

   * For JFIN
   * For plugins
   * For server-wide operations
   * For installation tasks

2. Keep your personal Jellyfin account **non-admin**

   * Preserves your watch history
   * Stops scripts/plugins from accidentally altering your data
   * Lets you see the UI exactly as normal users do
   * Adds a layer of safety if something goes haywire

This is the same best practice used by many Plex and Emby admins — one admin for automation, one normal admin for viewing.