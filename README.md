# Jellyfin Image Normalizer (JFIN)

Because why *wouldn’t* you build a tiny CLI for image resizing and then wrap it in config files, retries, backups, and a miniature observability stack?

JFIN (pronounced “jay-fin”, and absolutely *not* overthought) is a Python CLI that talks to the Jellyfin API, downloads your artwork, normalizes it, and uploads it back again — safely, cautiously, and with way more ceremony than strictly necessary.

Think: Fiat 500 engine, bolted into a full DTM race chassis.

---

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About the Project</a>
      <ul>
        <li><a href="#tldr">TL;DR</a></li>
        <li><a href="#what-problem-does-this-actually-solve">What problem does this solve?</a></li>
        <li><a href="#before--after">Before &amp; After</a></li>
        <li><a href="#feature-tour">Feature Tour</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#quick-start">Quick Start</a></li>
      </ul>
    </li>
    <li>
      <a href="#usage">Usage</a>
      <ul>
        <li><a href="#common-cli-examples">Common CLI Examples</a></li>
        <li><a href="#when-should-you-not-use-this">When should you not use this?</a></li>
      </ul>
    </li>
    <li><a href="#and-the-obligatory-disclaimer-this-is-not-a-backup-system">Backup &amp; Restore Warning</a></li>
    <li><a href="#documentation">Documentation</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#development">Development</a></li>
    <li><a href="#license">License</a></li>
  </ol>
</details>

---

## About the Project

### TL;DR

JFIN is a safe-by-default CLI tool that:

- Normalizes chaotic TMDb logos to a consistent canvas
- Resizes misclassified “thumb” backdrops to sane dimensions
- Optimizes oversized user profile images
- Talks only to Jellyfin’s HTTP API (no direct filesystem poking)
- Supports dry-runs, backups, and restore helpers so it’s very hard to misuse

If your Jellyfin UI looks inconsistent across devices, this tool exists for you.

### What problem does this actually solve?

Jellyfin already does a lot of smart caching and resizing. But a few specific image types still cause pain, especially in mixed-provider setups.

📢 Want a full list of arguments of why not to use TMDb plugin's scaling (that I spent much time thinking of)? Check out [Why not just use TMDb scaling?](docs/why-not-tmdb.md)

#### 1. Logos are chaos

Logos from TheMovieDatabase come in every size and ratio imaginable:

- `150 x 2000`, `750 x 90`, and everything in between  
- CSS skins like **ElegantFin** do their best, but wildly different aspect ratios still mean:
  - Logos jumping up and down between titles  
  - Some logos stretching across half the screen, others look tiny  

**JFIN’s logo mode:**

- Downloads logos through the Jellyfin API  
- Standardizes them to a consistent canvas (default `800 x 310`)  
- Scales and centers them on a transparent background  
- Optionally:
  - Only downscale
  - Only upscale
  - Skip padding entirely if you like your chaos centered differently

Result: logos that actually line up and behave. Your UI stops looking like a ransom collage.

#### 2. “Thumbs” that are actually full-size backdrops

The TMDb plugin likes to classify certain backdrops with text as `Thumb` images.  
That gives you “thumbs” that are:

- Full 4K, e.g. `3840 x 2160`
- Stored as-is in your metadata folder  
- Resized *at runtime* every time a client wants a friendly size  

Jellyfin handles that… but:

- Your metadata folder gets bloated
- You keep converting huge source files on-the-fly when there's a cache miss.

**JFIN’s thumb mode:**

- Finds item thumbs via the API (respecting libraries, operator, and filters)
- Rescales them to something sane (e.g. width `1000`, preserving aspect ratio via cover+crop)
- Re-uploads optimized JPEGs with configurable quality  
- Often cuts your thumb storage roughly in half (*results may vary; claims made are not indicative of actual performance*) without you ever noticing visually.

You still get nice images — just without the “why is my metadata folder this big?” moment.

#### 3. User profile images bypass the cache

Profile images seem to dodge the normal caching pipeline.  
Upload an 8MB+ selfie and Jellyfin will politely serve it on every dashboard view.

**JFIN’s profile mode:**

- Fetches all active users
- Grabs their profile images directly
- Normalizes them to a default `256 x 256` WebP (with alpha preserved)
- Re-uploads the optimized version for each user

That means:

- Faster dashboard loads
- Smaller avatar payloads
- No more accidentally using a poster-sized PNG as your profile pic

### Before & After

Logos look fine in isolation — the chaos only becomes obvious when you see them side-by-side, displayed on an actual device.

You can see real-world comparisons for Desktop (QHD), Tablet (WQXGA), and Mobile (20:9, 1116×2484) here:

👉 [Before & After: Real-World Results](docs/before-and-after-comparison.md)

### Feature Tour

At a glance, JFIN gives you:

- 🔍 **API-only discovery**  
  Talks only to Jellyfin’s HTTP API (no direct filesystem poking), using a dedicated operator user and optional library filters.

- 🖼 **Three focused modes**  
  `logo`, `thumb`, and `profile` — each with its own canvas, format, and scaling rules tuned for Jellyfin’s UI.

- 🧪 **Safe-by-default behavior**  
  `dry_run = true` in the generated config, hard blocking of POST/DELETE while dry-run is on, and optional backups before any writes.

- 🔧 **Configurable, but not fragile**  
  Per-mode width/height/quality, scaling guards like `no_upscale` / `no_downscale`, optional padding for logos, timeouts, retries, and throttling.

- 📝 **Logging and automation friendly**  
  CLI + file logging, optional silent mode for cron, and a design that makes it easy to run periodically or inside the Jellyfin container.

👉 Check out the full feature breakdown and details: [Feature Tour](docs/feature-tour.md)

---

## Getting Started

### Prerequisites

- A running Jellyfin server with API access
- A Jellyfin API key for an operator/maintenance user
- **Python 3.11+**

✨ A full example configuration is included as `config.example.toml`.

### Installation

Requires **Python 3.11+**.

```bash
git clone https://github.com/your-user/jellyfin-image-normalizer.git
cd jellyfin-image-normalizer
pip install -r requirements.txt
````

This gives you:

* `jfin.py` – the CLI entry point
* `jfin_core/` – the overengineered engine room

### Quick Start

1. **Create an API key in Jellyfin** (requires admin rights)

   - Go to `JELLYFIN_URL/web/#/dashboard/keys`
   
   - Click on `New API Key`

   - Give the API key a name, e.g., `JFIN`, and click `Create`

   - Save the API key for later use in the `config.toml`

2. **Generate a config template**

   ```bash
   python jfin.py --generate-config
   ```

3. **Edit your `config.toml`**

   At minimum:

   ```toml
   [SERVER]
   jf_url     = "https://your-jellyfin.example"
   jf_api_key = "YOUR_API_KEY"

   [MODES]
   operations = ["logo", "thumb", "profile"] # or a subset

   [API]
   dry_run    = true        # keep this true until you’re happy

   [BACKUP]
   backup     = true
   ```

   Optional but recommended:

   ```toml
   [operator]
   username = "your-jellyfin-username"

   [libraries]
   names = ["Movies", "TV Shows"] # or nothing "[]" to process all movie and tv show libraries
   ```

4. **Test connectivity (no images harmed)**

   ```bash
   python jfin.py --test-jf
   ```

5. **Do a full dry-run**

   ```bash
   python jfin.py --dry-run
   ```

   This will:
   * Discover libraries/items
   * Plan all scaling operations
   * Log what *would* be uploaded
   * Not touch Jellyfin at all

   💡 You can keep dry_run = true in config and/or use --dry-run from CLI

6. **Enable actual uploads (when you’re ready)**

   In `config.toml`:

   ```toml
   dry_run       = false
   ```

   Then run:

   ```bash
   python jfin.py
   ```

   ❗ Remember to use `--config` flag if your `config.toml` does not live with `jfin.py`.

   Now the magic happens (plus backups, if enabled).

---

## Usage

### Common CLI Examples

Normalize according to settings in `config.toml`:

```bash
python jfin.py
```

Overwrite mode in `config.toml` and only fix logos:

```bash
python jfin.py --mode=logo
```

Override logo size and disable padding (for the minimalists):

```bash
python jfin.py --mode=logo \
  --width 500 --height 200 --no-padding
```

Override mode and fix thumbs (and resize those “4K thumbs”):

```bash
python jfin.py --mode=thumb --width 1000
```

Override mode and process profile images for a single user:

```bash
python jfin.py --mode=profile --single some_username
```

Restore logos from backups (all items for one mode):

```bash
python jfin.py --mode=logo --restore
```

Restore everything:

```bash
python jfin.py --restore-all
```

### When should you *not* use this?

* If you’re happy with totally random logo sizes
* If disk usage and avatar payloads don’t bother you at all
* If the phrase “backup-aware dry-run image normalizer for a media server” makes you physically uncomfortable

Otherwise, JFIN gives you:

* Cleaner, more consistent artwork
* Smaller, saner image assets
* The smug satisfaction of knowing your Jellyfin is *very* slightly more polished than it needs to be

---

## ⚠️ And the obligatory Disclaimer: This is NOT a backup system

JFIN includes a “backup” and “restore” function, but these are **not real backups** in the Jellyfin sense.

Short version:

* JFIN only backs up the image files it processed — nothing more, nothing less.
* It does **not** back up Jellyfin’s database, item UUID mappings, watch history, playlists, subtitles, chapters, or anything outside the specific images JFIN touched.
* If Jellyfin re-imports your media and UUIDs change, JFIN cannot restore images to items that no longer exist under the same ID.

Jellyfin 10.11+ provides a robust, official, database-aware backup + restore.
Use *that* for real server recovery, and treat JFIN’s backups as a convenience utility only.

👉 Full details and edge cases: [Backups, UUIDs, and what JFIN can’t restore](docs/backups-and-uuids.md)

---

## Documentation

Additional documentation lives in the `docs/` folder:

* [Before & After comparisons](docs/before-and-after-comparison.md)
* [Why not just use TMDb scaling?](docs/why-not-tmdb.md)
* [Feature tour (full details)](docs/feature-tour.md)
* [Backups, UUIDs, and restore limitations](docs/backups-and-uuids.md)
* [Advanced usage & tips](docs/advanced-usage.md)
* [Cron, Docker, and LSIO container setups](docs/docker-and-cron.md)
* [Provider behavior & canvas size choices](docs/provider-behavior.md)
* [Technical notes and internals](docs/TECHNICAL_NOTES.md)


---

## Contributing

Contributions, bug reports, and “why did you build *this*?” issues are all welcome.

If you want to hack on JFIN:

* Fork the repo
* Make your changes in a feature branch
* Add or update tests where it makes sense
* Run the test suite (see below)
* Open a pull request

For internal architecture and layout, see: [Technical Notes](docs/TECHNICAL_NOTES.md).

---

## Development

* Code lives in `jfin_core/`
* CLI entry is `jfin.py`
* Dependencies are listed in `requirements.txt`

Run tests:

```bash
python -m pytest
```

More details about the processing pipeline, classes, config TOML, and CLI entrypoints are documented in:

* [Technical Notes](docs/TECHNICAL_NOTES.md)

---

## License

This project is licensed under GPL-3.0. See the `LICENSE` file for details.