# Architecture
Status: proposed design; no implementation or transport validation.

## Scope and invariants
Elune's Gaze — A Second Window into Azeroth is a read-only WoW Retail second-screen project. Initial scope is permitted noncombat chat, quest state, and read-only map context. Every field requires review against the current Retail API and Blizzard policy before implementation.

No process-memory reads, injection, hooks into game internals, input synthesis, gameplay automation, protected/secret-value extraction, or circumvention of API restrictions. Never coerce, inspect, encode, or otherwise expose a restricted value. A missing capability remains unavailable. No combat telemetry or combat assistance is in scope.

## Proposed data flow
Retail supported Lua APIs
  -> allowlisted noncombat collectors
  -> sanitized, bounded records
  -> experimental visible pixel panel
  -> OS screen-capture backend
  -> decoder and schema validation
  -> local state service
  -> read-only browser dashboard

This describes a hypothesis, not a validated transport. A visible pixel panel and external capture do not establish acceptability under Blizzard policy. Stop transport work if review cannot establish a permissible path.

## Retail Lua addon
Event-driven collectors for opt-in chat, quest state, and supported map context. Use only ordinary values explicitly available for this purpose; omit unavailable fields. Pause collection and experimental publication during combat; clear pending records and invalidate stale state. Guard every collector independently rather than treating combat state alone as permission.

Bound record sizes and update rates to limit UI cost. No sockets or arbitrary filesystem transport are assumed. SavedVariables may hold user configuration, never a promise of a live data channel. Do not ship a guessed Retail interface version.

## Experimental pixel bridge
Research-only candidate: render a small visible addon-owned color grid and decode its captured image. Before any live trial, review policy and APIs; use synthetic fixtures for initial codec research.

A candidate framing scheme should include a protocol version, session identifier, record type, sequence number, payload length, and checksum. Checksums detect corruption, not malicious tampering. Set hard bounds before allocation. Reject malformed, unsupported, truncated, replayed, or stale records. Use periodic full snapshots to recover from dropped frames without a return channel.

Unresolved: color management, HDR, scaling, antialiasing, compression, window occlusion, frame loss, bandwidth, latency, and OS permissions. No performance, reliability, or compatibility claim is made.

## Cross-platform companion
Share decoder, schema validation, state store, and local web service across Windows and Linux/SteamOS. Keep native capture behind an interface:
- enumerate user-selectable sources and report capabilities;
- request capture through supported OS consent;
- start/stop a selected source and deliver timestamped frames;
- report permission denial, source loss, and unsupported modes.

Candidate backends to investigate include supported Windows capture APIs and Linux portal/PipeWire capture where available. X11 and SteamOS gaming-mode behavior require separate evaluation. These are research targets, not promised supported backends. Never bypass compositor or OS capture restrictions. Prefer a user-selected window/region, discard raw frames promptly, and provide an obvious capture stop control.

## Local service and dashboard
Serve bundled assets and a read-only snapshot/event API from one local companion. Default bind is loopback. An explicit user setting enables a selected private LAN interface; do not configure router forwarding or public exposure.

LAN mode requires paired clients with revocable credentials, authenticated data requests and event streams, origin/host validation, bounded requests, and an encrypted connection before private chat is shared. Specify the pairing and certificate UX before implementing LAN access. Avoid permissive CORS and cross-site socket access. Dashboard interactions only filter or navigate local views; no game commands, chat sending, quest acceptance, or map control in WoW.

Chat, quests, and map views show source timestamps, connection state, and a visible stale indicator. Read-only map content must come from permitted sources with appropriate asset rights; do not assume Blizzard art can be redistributed.

## Privacy and trust
Chat export is opt-in and off by default, with separate channel selection. Keep state in memory by default; no raw capture retention, telemetry, cloud relay, or message-content logs. Provide clear-session and disconnect controls. Any persistence needs a separate retention choice. Treat decoded text as untrusted: escape dashboard output and validate every record. LAN access can expose character and chat information to paired devices.

## Suggested repository layout
- addon/ — Retail Lua addon (future)
- companion/ — shared service and capture adapters (future)
- dashboard/ — browser client (future)
- protocol/ — schema, synthetic fixtures, codec notes (future)
- docs/ — research evidence and decisions (future)

Directories above are planned, not implemented. Companion runtime, UI framework, packaging, and release automation remain open decisions.

## Research and delivery gates
1. Document current policy and field-by-field API constraints, including combat transitions and restricted values. Resolve whether a pixel bridge may proceed.
2. Test a synthetic codec offline across scaling, color changes, corruption, frame drops, and strict input bounds.
3. Evaluate capture with OS consent on Windows and Linux/SteamOS; record exact tested environments and limitations.
4. Only after review, trial a minimal permitted live noncombat field; verify immediate suspension and stale-state behavior.
5. Build a loopback dashboard before opt-in authenticated, encrypted LAN sharing.
6. Publish compatibility and limitations only with reproducible evidence; stop or redesign if a required gate fails.

No live-game tests, policy review, or transport tests have been performed by this repository initialization.
