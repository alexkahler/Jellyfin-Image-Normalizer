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

````

---

## `docs/docker-and-cron.md`

```markdown
# Cron, Docker, and Running JFIN in the Jellyfin Container

## Running JFIN as a Scheduled Cron Job

You can use all CLI flags when setting up your cron job, enabling you to fully customize how and when `jfin.py` processes your images, including with different config files via `--config "/path/to/custom/config.toml"` for different Jellyfin installs:

```bash
0 3 * * * /usr/bin/python3 /path/to/jfin.py -s
````

`-s` / `--silent` suppresses **CLI output only** — the run will still produce logs using whatever file logger you configured in `config.toml`.
This keeps cron quiet while preserving full logging.

If you prefer to capture CLI output as well, you can redirect it:

```bash
0 3 * * * /usr/bin/python3 /path/to/jfin.py >> /var/log/jfin_cron.log 2>&1
```

---

## Running JFIN inside the LSIO Jellyfin container (recommended)

If you use [LinuxServer.io’s Jellyfin](https://docs.linuxserver.io/images/docker-jellyfin/) image (which you probably should, thanks to PUID/PGID support, easy hardware-acceleration mods, and more), you can run JFIN *inside the Jellyfin container* using LSIO’s **universal-cron** mod:

* [Universal-Cron](https://github.com/linuxserver/docker-mods/tree/universal-cron)
* [HW Accel Mods](https://mods.linuxserver.io/?mod=jellyfin)
* Further reading on Docker Security & PUID/PGID:
  [Understanding PUID and PGID](https://docs.linuxserver.io/general/understanding-puid-and-pgid/#using-the-variables)
  [Docker Security Practices](https://www.linuxserver.io/blog/docker-security-practices)

**Why run JFIN inside the container?**

* All API traffic stays internal (`localhost`)
* Cleaner networking (no exposing Jellyfin URLs)
* One self-contained environment to manage
* Cron survives container restarts via `/config/crontabs/root`

**How to set it up:**

1. Create a `scripts` folder under `/config` for your `jfin.py` + config.
2. Install the universal-cron mod by updating your Docker compose.
3. After the mod generates `/config/crontabs/root`, edit that file to schedule JFIN.

This approach keeps everything isolated, predictable, and secure — just how LSIO likes it.
