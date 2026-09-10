# iPad Photo Frame — Home Assistant integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration for [PhotoFrame](https://github.com/superbam/PictureFrame),
the iPadOS app that turns a wall-mounted iPad into a digital photo frame.
Talks to the app's built-in local REST API — no cloud dependency, no MQTT
broker required.

Frames advertise themselves over Bonjour (`_photoframe._tcp`), so most
installs are a discovery card away from working; multiple frames are just
multiple config entries.

## Install

**Via HACS (recommended):**
1. HACS → the "⋮" menu (top right) → Custom repositories.
2. Repository: `https://github.com/superbam/homeassistant-photoframe`, category: Integration.
3. Install "iPad Photo Frame", then restart Home Assistant.

**Manually:** copy `custom_components/photoframe` into your Home Assistant
config's `custom_components/` directory, then restart.

## Add a frame

- **Discovered automatically** — Settings → Devices & Services shows a
  discovery card for each frame Home Assistant sees over mDNS. Click it,
  enter the username/password from the frame's Settings screen (Display →
  Password → the eye icon), done.
- **Manual** — Settings → Devices & Services → Add Integration → "iPad Photo
  Frame", then enter host/IP, port (default `8080`), username, and password.
  Use this when Home Assistant and the frame are on different VLANs/subnets
  that mDNS doesn't cross.

The frame's self-signed TLS certificate (there's no public DNS name to get a
real one for) is handled automatically — nothing to configure.

## Entities

Each frame becomes one device. Close to everything on the web settings page
has a matching entity:

| Entity | What it does |
|---|---|
| `light.<frame>_display` | On/off (via `/api/display` — the same non-destructive blank/wake override the web page's "Blank now"/"Wake now" buttons use) and brightness (via `/api/brightness`, which persists the on-brightness, same as the web page's slider) |
| `sensor.<frame>_photos` | Photo count |
| `sensor.<frame>_slide_position` | Current index, with total/kind/id/date as attributes |
| `sensor.<frame>_memory_usage`, `_peak_memory_usage` | Diagnostics |
| `sensor.<frame>_last_library_sync` | Timestamp of the last iCloud shared-album sync |
| `sensor.<frame>_schedule_on_time`, `_schedule_off_time` | Read-only — the JSON settings API doesn't accept writes to the schedule clock times, only the HTML form does |
| `binary_sensor.<frame>_paused` | Playback state (not a persisted setting — toggle it with the play/pause buttons below) |
| `button.<frame>_next_slide`, `_previous_slide`, `_play`, `_pause`, `_ping_presence` | One-shot actions |
| `switch.<frame>_*` | Every boolean setting: mute video, shuffle, schedule enabled, motion blanking, external presence, collage mode, randomize transitions, blur edges, show clock/caption/location/weather/calendar, use device location for weather, 24-hour clock, video-plays-to-completion, Live Photo playback/repeat/loop/per-photo overrides, download cache |
| `number.<frame>_brightness` | Plain 0-100% brightness slider (via `/api/brightness`, same endpoint the light entity's brightness and the web page's own slider use) |
| `number.<frame>_*` | Slide duration, transition duration, blur amount, motion blank timeout, download cache cap, Live Photo trim start/end |
| `select.<frame>_*` | Transition style (all 10), scale mode (fit/fill), clock size, collage grid size (2/4/6) |
| `text.<frame>_weather_location` | Manual weather location (when not using device location) |

Deliberately **not** exposed, with reasons:
- `webServerEnabled` — turning it off from Home Assistant would sever the
  very connection this integration uses; the one setting that could brick
  itself from inside itself.
- `frameName`, `webUsername` — editing either risks breaking this config
  entry's stored identity/auth.
- Frame sync (`syncFrames`/`syncAlbum`/`syncGroupCode`), calendar selection,
  and shared-album selection — each needs a picker over a list the device
  itself holds (its own calendars/albums), which there's no endpoint to
  fetch; better done on the frame directly for now.

Polling interval defaults to 30s, adjustable per frame via the integration's
"Configure" options — but that's now a fallback, not the primary path. See
below.

## Instant on/off updates (webhook)

By default, `light.<frame>_display`'s on/off state is only as fresh as the
last poll — up to the configured interval — which is slow for a
schedule/presence-triggered blank or wake that happens on the frame itself
rather than through Home Assistant.

No setup needed — on every startup/reload, the integration generates a
webhook URL and writes it to the frame's `haWebhookURL` setting through the
same authenticated connection it already polls with (a no-op once it's
already set correctly, so this doesn't spam the frame with writes on every
restart). The frame then POSTs its on/off state there the instant it
changes. If the frame's unreachable at that moment, it falls back to a
persistent notification with the URL to paste in yourself (web settings
page, or the on-device Settings screen) — auto-configuring picks back up on
the next restart, and the notification dismisses itself once a push arrives.
Clearing `haWebhookURL` on the frame (or removing the integration, which
clears it for you) disables this entirely; polling still works exactly as
before either way.

This isn't a replacement for polling, it's a supplement: if nothing (a push
or a poll) has been heard from the frame in one fallback-polling-interval's
worth of time, the coordinator polls for real, same as always. In practice
that means a configured webhook makes real polling rare rather than
eliminating it — actual request volume against the frame goes *down*
compared to tightening the poll interval, since a push only fires on real
transitions instead of every tick regardless of change.

## Notes

- The app must be in the foreground for its server to run — normal for a
  wall-mounted, always-on frame.
- Every setting the web page's HTML form can write, the JSON settings API can
  too, with one exception: the schedule's on/off clock times (see the table
  above) — those stay read-only here.
- The app's REST API is documented directly in the main repo's
  [`HomeAssistant.md`](https://github.com/superbam/PictureFrame/blob/main/HomeAssistant.md).
