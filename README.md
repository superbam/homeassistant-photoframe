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

Each frame becomes one device with:

| Entity | What it does |
|---|---|
| `light.<frame>_display` | On/off and brightness, mapped to `/api/brightness` (brightness `0` blanks the screen) |
| `sensor.<frame>_photos` | Photo count |
| `sensor.<frame>_slide_position` | Current index, with total/kind/id/date as attributes |
| `sensor.<frame>_slide_duration`, `_transition_style` | Playback settings |
| `sensor.<frame>_memory_usage`, `_peak_memory_usage` | Diagnostics |
| `sensor.<frame>_last_library_sync` | Timestamp of the last iCloud shared-album sync |
| `binary_sensor.<frame>_muted`, `_paused`, `_shuffle`, `_schedule_enabled` | Status flags |
| `button.<frame>_next_slide`, `_previous_slide`, `_play`, `_pause`, `_ping_presence` | One-shot actions |

Polling interval defaults to 30s, adjustable per frame via the integration's
"Configure" options.

## Notes

- The app must be in the foreground for its server to run — normal for a
  wall-mounted, always-on frame.
- This integration only covers what `/api/status` exposes. For anything
  else, the app's REST API is documented directly in the main repo's
  [`HomeAssistant.md`](https://github.com/superbam/PictureFrame/blob/main/HomeAssistant.md).
