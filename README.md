# Elune's Gaze
## A Second Window into Azeroth

An open-source project exploring a read-only second-screen experience for World of Warcraft Retail: permitted noncombat chat, quests, and map context in a local browser dashboard.

**Status: experimental personal transport lab available in [poc/](poc/README.md). Offline codec tests pass; live WoW behavior and transport reliability are unvalidated. No companion service is included.** The proposed pixel-encoded data bridge is an **unvalidated proof of concept**, subject to Blizzard policy and technical investigation. Screen capture does not establish policy approval. There is no claim of Blizzard approval, transport reliability, or current API compatibility.

### Planned components
- **Retail Lua addon:** collect only explicitly permitted, ordinary noncombat data through supported addon APIs.
- **Companion:** Windows and Linux/SteamOS support through modular screen-capture backends.
- **Experimental bridge:** addon-rendered pixels captured and decoded by the companion, only if policy and feasibility review supports proceeding.
- **Browser dashboard:** locally hosted chat, quest, and read-only map views; opt-in LAN access for a second device.

### Boundaries
Read-only with respect to the game. No memory injection or process-memory access, input automation, protected/secret-value extraction, restriction bypasses, or combat assistance. Browser actions must not send commands back into WoW. Unavailable or restricted data is omitted.

### Getting started
Read [ARCHITECTURE.md](ARCHITECTURE.md) for components, trust boundaries, research gates, and proposed milestones. For the personal addon and screenshot decoder, follow [poc/README.md](poc/README.md). Implementation language and framework for the companion and dashboard remain undecided.

Chat can contain private information. The design keeps data local, disables chat export by default, and requires explicit LAN sharing and client pairing.

This is an independent fan project, not affiliated with or endorsed by Blizzard Entertainment. World of Warcraft and related names belong to their respective owners.

### License
Copyright (C) 2026 Fiordhraoi and contributors.

Elune's Gaze is licensed under the GNU General Public License version 3 only (SPDX: `GPL-3.0-only`). See [LICENSE](LICENSE) for the full terms. Distributed without warranty.
