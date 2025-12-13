# Why not just use the TMDb plugin’s image scaling (and other questions)?

Excellent question. Short answer: because it’s convenient… for TMDb, not for you.

Longer answer:

- **Limited scaling presets**  
  TMDb’s API only exposes a small set of sizes **per image type**.  
  For backdrops you get things like `w300`, `w780`, `w1280` — and that’s it.  
  Want a nice clean Full HD backdrop and a small thumb? Too bad.

- **Backdrops moonlighting as thumbs**  
  The TMDb plugin treats some text-bearing backdrops as `Thumb` images.  
  If you choose `w780` for “thumbs”, that setting also controls backdrops.  
  So you either:
  - Get “thumbs” that are way larger than needed, or  
  - Cap your backdrops to a low resolution forever.

- **Resolution information disappears**  
  When you enable TMDb scaling, the Jellyfin UI stops showing the image’s original resolution in the picker.  
  That makes it impossible to tell:
  - Which image is high-res  
  - Which one is a resized, heavily compressed relic from another site  
  - Which ones are worth keeping  
  To see resolutions again, you have to turn scaling back to `original`.

- **Better workflow: download originals, then normalize yourself**  
  Given all of the above, it’s usually better to:
  1. Tell TMDb to give you **original-size** artwork.  
  2. Let Jellyfin stash that on disk.  
  3. Use something like JFIN to rescale, pad, and optimize images the way *you* want.

- **“Why not just use Fanart / TheTVDb instead?”**  
  They’re great as additional sources and you absolutely can (and probably should) use them too.  
  But in practice:
  - TMDb has the **largest** and most actively maintained set of movie posters.  
  - Posters are often **higher quality** and ranked by community votes, so the “auto-picked” poster is usually the best one.  
  - Fanart/TheTVDb tend to have a smaller selection of Movie posters/logos.  

- **Also Remember: Mixed-source artwork means mixed padding rules**  
  If you use **TMDb**, **TheTVDb**, and **Fanart** together (which most people do), you’re probably already getting *padded* logos — just not consistently.

  Why?

  - **TheTVDb** and **Fanart** both normalize their logos to **800×310**, and they  
    - Scale the logo  
    - Add transparent padding to fill negative space  
    - Deliver perfectly canvas-sized images  

  - **TMDb**, on the other hand, does *not* pad or enforce a standard canvas.  
    Its logos arrive in whatever weird and wonderful size and ratio their contributors uploaded.

  On an average, long-running library with mixed metadata sources, this means you end up with:
  
  - Some logos with padding  
  - Some without padding  
  - Some ultra-wide  
  - Some extremely short  
  - And all of them subject to **metadata ranking order**, meaning the chosen logo may change based on provider order.

  Result:  
  A grid where half your logos sit nicely aligned (from Fanart/TVDb), and the other half bounce around like they’ve had too much caffeine (from TMDb).  

  **JFIN fixes this by enforcing one canvas, one scale rule, no matter where the logo originally came from.**

- **The “real reason this script exists”: long anime titles + unpadded logos = overlap chaos**  
  Some series have very long display titles — especially when you show both the English title *and* the original title (or season titles that include both). On certain Jellyfin skins and layouts, an unpadded logo can sit so low that the text overlaps the bottom of the logo, creating a cramped, cluttered look.

  By enforcing a consistent logo canvas and adding transparent padding, JFIN effectively *lifts* the logo a little higher. That extra breathing room prevents text overlap and makes even long-title anime entries look clean and intentional across different device sizes.

  While some themes have improved this behavior, many skins (and some official layouts) still exhibit subtle overlap issues — especially with multi-line titles. Normalizing logos ensures they stay safely out of the way, independent of client CSS quirks.

So the idea is: let TMDb be your high-quality raw source, optionally have TheTVDb and Fanart as backup sources, then use JFIN to turn that into clean, consistent, Jelly-friendly artwork.


## **“Why not just let Jellyfin resize everything through its internal image URLs?”**

Another great question — and the answer comes down to how Jellyfin handles caching behind the scenes.

* **Jellyfin always caches every resized image you request**
  
  When you hit a URL like
  `…/Items/{id}/Images/Primary?maxWidth=800&quality=90`
  Jellyfin doesn’t just stream you a resized image.
  It also **stores that resized version in its internal cache** - because Jellyfin assumes that if *one* client requested that size once, *other* clients might need it later. Or *you* might need it again. I mean, god forbid, what if?

* **Batch-processing your whole library explodes the cache**
 
  If your script pulls thousands of thumbs, backdrops, and logos at various sizes, Jellyfin will happily cache **every single one** of those resized derivatives.
  You may never request them again, but they’ll still sit there on disk, bloating your `cache/` directory with images that serve only the script - not real clients.

  In a full-library processing pass, this can generate:

  * Dozens of resized variants per item
  * Plenty of cached files
  * And potentially gigabytes of unnecessary cache churn

* **Cache churn = slower scans + wasted I/O + increased fragmentation**
  
  Jellyfin’s cache isn’t free.
  More items means:

  * Longer cache cleanup cycles
  * More file writes on spinning disks or SSDs
  * Higher I/O latency during heavy metadata operations
  * Unpredictable eviction behavior if the cache grows too fast

  All of this happens **just because the script asked Jellyfin to resize images it never needed to serve to a real user**.

* **Better workflow: bypass Jellyfin, download once, optimize locally**
  
  Instead of involving Jellyfin’s cache at all:

  1. Bypess Jellyfin's cache and download the **original** images directly.
  2. Resize, pad, convert, and normalize them using **Pillow**.
  3. Upload the final,normalized version that Jellyfin should display.

  This approach has clear advantages:

  * **Zero Jellyfin cache pollution**
  * **Faster processing** because local resizing avoids HTTP overhead and won't burden your server.
  * **Predictable, repeatable** results (Jellyfin’s scaling rules can change between versions).
  * **Full control** over padding, quality, and canvas size.

* **In short:**
  
  If Jellyfin does the resizing → you get **hidden side effects** and an oversized cache.
  If you do the resizing → you get **clean, consistent artwork** with no Jellyfin side-effects.
