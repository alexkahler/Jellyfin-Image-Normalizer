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

## Running JFIN inside the LSIO Jellyfin container (this is totally unecessary)

If you use [LinuxServer.io’s Jellyfin](https://docs.linuxserver.io/images/docker-jellyfin/) image (which you probably should, thanks to PUID/PGID support, easy hardware-acceleration mods, and more), you can run JFIN *inside the Jellyfin container* using LSIO’s **universal-cron** and **universal-package-install** mod:

* [universal-cron](https://github.com/linuxserver/docker-mods/tree/universal-cron)
* [universal-package-install](https://github.com/linuxserver/docker-mods/tree/universal-package-install)
* [HW Accel Mods](https://mods.linuxserver.io/?mod=jellyfin)
* Further reading on Docker Security & PUID/PGID:
  [Understanding PUID and PGID](https://docs.linuxserver.io/general/understanding-puid-and-pgid/#using-the-variables)
  [Docker Security Practices](https://www.linuxserver.io/blog/docker-security-practices)

**Why run JFIN inside the container?**

* All API traffic stays internal (`localhost`)
* Clean coupling between Jellyfin and JFIN
* One self-contained environment to manage
* Cron survives container restarts via `/config/crontabs/root`

**Why not to set it up?**

* Come on, to be fair. This is a bit over the top, innit?

**How to set it up:**

1. Create a `scripts` folder under `/config` for your `jfin.py` + config.
2. Install the universal-cron and universal-package-install mod by updating your Docker compose.
3. Add `INSTALL_PACKAGES=python3` and `INSTALL_PIP_PACKAGES=requests|Pillow|tomli`
4. After the mod generates `/config/crontabs/root`, edit that file to schedule JFIN.

This approach keeps everything isolated, predictable, and secure — just how LSIO likes it.