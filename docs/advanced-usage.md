# Advanced Usage & Tips

This page collects small but useful patterns and best practices that don't fit in the basic README examples.

---

## Force-register a manually replaced image

If you manually replace an image inside your Jellyfin metadata folder and Jellyfin refuses to acknowledge it (cache might not be updated or the old image size is still shown), you can force JFIN to re-upload the file:

```bash
python jfin.py --single <item_uuid> \
  --force-upload-noscale \
  --width <image_width> \
  --height <image_height>
```

This forces Jellyfin to associate the new file with the item, even if the dimensions didn't change.

---

## Target only movies or series

Use `--item-types` to constrain discovery to specific Jellyfin item types. This overrides the `[modes].item_types` config value for the run:

```bash
# Only process series for logo/thumb discovery
python jfin.py --mode logo --item-types series
```

You can also combine values: `--item-types movies|series` (default) or set the same option in `config.toml` under `[modes].item_types`.

## Use a Maintenance Account

When administering a media server or any self-hosted application stack, it is good practice to separate
**daily-use accounts** from **automation or maintenance accounts**.  
This helps protect user data, reduce accidental changes, and keep administrative tasks cleanly isolated.

### Why create a dedicated maintenance account?

A maintenance/admin account typically has:

* Full access to all libraries or resources
* No parental-control or visibility restrictions
* No content tags, filters, or profile limitations
* No personal watch history, usage activity, or preferences that matter

This ensures automated tasks, scripts, plugins, or administrative tools can operate without
interfering with day-to-day user data or UI personalization.

### Recommended pattern

1. **Create a “maintenance” account**
   * Used for automation tools  
   * Used for plugin/configuration work  
   * Used for low-level or system-wide administrative operations  
   * Not used for personal media consumption  

2. **Keep your personal account non-privileged**
   * Preserves your own watch history and recommendations  
   * Prevents automations from accidentally modifying your profile  
   * Allows you to experience the UI exactly as regular users do  
   * Adds a layer of safety if a script or integration behaves unexpectedly  

This principle of separating personal and administrative accounts is widely used and it helps maintain consistency,
safety, and long-term maintainability of your environment.
