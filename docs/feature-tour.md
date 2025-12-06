# Feature Tour

A very serious tool for a very specific job.

## API-based discovery

- Talks only to Jellyfin’s HTTP API. No direct filesystem poking. *poke poke.*  
- External library support. Your artwork cohabitates with your Scarlett Johansson? No problem!  
- Uses an “operator” user to discover libraries and items. Yes, you're a Tier 1 Operator now.  
- Filters by library names (`Movies`, `Shows`, etc.) when you want.  

## Three distinct modes

- `logo` – Transparent PNG canvas (default `800x310`), optional padding, palette-aware.  
- `thumb` – Landscape JPEG via cover+crop, tuned for library grids.  
- `profile` – Square WebP avatars for all users (or a single user).  

## Backups & Restore

- Optional backup of originals before upload.  
- Two strategies:
  - `partial` – back up only images that were actually rescaled.  
  - `full` – back up everything touched.  
- Restore paths:
  - Per-mode restore (`--restore --mode logo|thumb|profile`)  
  - Full restore of all backups (`--restore-all`)  
  - Single item/user restore (`--restore --single ...`)  

## Extremely safe by default

- `dry_run = true` in the generated config.  
- Actually blocks POST/DELETE when:
  - `dry_run = true`, or  
  - Writes only happen when dry_run = false.  
- Writes only happen when you scream “yes” in TOML.  

## Ridiculous amount of configurability

- Per-mode width/height, quality, and scaling rules:
  - `no_upscale`, `no_downscale`  
  - `no_padding` (logo only)  
  - `force_upload_noscale` if you want re-uploads even when size doesn’t change  
- API behavior:
  - TLS verification, timeouts, throttle between requests  
  - Retry count and backoff  
  - `fail_fast` mode for when you’re in a mood  
- Logging:
  - CLI + file logging  
  - Verbose/silent modes  
  - Run IDs and summary stats  
