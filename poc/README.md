# Elune's Gaze - personal transport lab 0.1.0

Experimental Retail Lua addon plus an offline Python screenshot reader. No companion service or continuous capture yet. Not tested in a live WoW client, not Blizzard approved, and not a validated transport. The developer's policy inquiry is pending. Synthetic mode is the recommended first experiment.

## 1. Prepare and install

In your Retail client, run `/dump select(4, GetBuildInfo())` and note the interface number. Close WoW. No client version is guessed or claimed supported by this package.

On Linux/SteamOS, from this extracted directory, run (your reported interface number is 120105):

```sh
sh ./prepare-addon.sh 120105
```

No executable permission or PowerShell is needed. The script also works when invoked from another directory. For a different client version, substitute the interface number reported by that client.

On Windows in PowerShell, run:

```powershell
.\Prepare-Addon.ps1 -InterfaceVersion YOUR_NUMBER
```

Replace YOUR_NUMBER with the integer returned by your client. Both scripts create the .toc locally and refuse to overwrite an existing one; neither installs anything. Alternatively, copy ElunesGazePoC.toc.in to ElunesGazePoC.toc yourself and replace @INTERFACE@ with that number in a text editor (do not leave it as .toc.txt).

Copy the ElunesGazePoC folder to your actual `_retail_/Interface/AddOns/` directory. Verify the final path is `Interface/AddOns/ElunesGazePoC/ElunesGazePoC.toc`. Start WoW and enable Elune's Gaze - Transport Lab. Matching the interface number is not proof of API compatibility.

## 2. First screenshot test

In a quiet noncombat location:

1. `/egp sample` displays a fixed known message twice, then an idle packet. To capture the sample easily, first use `/egp rate 1` (one second per frame), then `/egp sample` and promptly take a lossless screenshot. An idle packet is also a valid decode.
2. `/egp test` continuously emits numbered synthetic records, once per second. This samples no quest/chat data. Start at the default 2 Hz publication rate.
3. The strip defaults to Slim (16x256 physical pixels), eight pixels from the lower-left edge. `/egp fat` changes it to 32x128. `/egp unlock` lets you drag the strip; `/egp lock` locks it. `/egp reset` restores the corner.
4. Capture a native-resolution PNG with no resizing. Avoid JPEG, HDR conversion, streaming compression, or overlapping UI. A Windows PNG screenshot is a good first test. Do not post full screenshots containing private chat.
5. `/egp off` disables the strip, stream and chat sampling. Output and sampling always start OFF after reload/login. Combat hides the strip and discards queued packets; it resumes with idle after combat. No combat data is collected.

## 3. Read the image (Windows or Linux)

Install Python 3.10+ and Pillow, then run from the extracted folder:

```text
python -m pip install -r requirements.txt
python make_fixtures.py
python read_strip.py fixtures/slim.png
python read_strip.py "your-screenshot.png"
```

The reader searches for the upper-right keystone automatically, identifies Slim/Fat, verifies framing and the Fletcher-16 checksum, and prints the decoded text. No network access, image upload, game access, or screen capture occurs in this script.

If automatic detection fails, supply the strip's TOP-LEFT image coordinates (not its lower-left game anchor):

```text
python read_strip.py "your-screenshot.png" --layout slim --x 8 --y 816
```

The example y=816 applies ONLY to a 1080-pixel-high game image with a 256-pixel strip and an 8-pixel bottom margin. Desktop borders, window offsets and other resolutions change coordinates. The design targets physical pixels, but actual sizing must be verified on your client/display. Only native 4x4 cells are supported in this first reader.

Long messages span packets. One screenshot proves only the captured fragment is readable. Supply screenshots from the SAME addon session to reconstruct a complete record:

```text
python read_strip.py first.png second.png third.png
```

Exit codes: 0 = all supplied packets valid and messages complete; 1 = file/decode failure; 2 = valid packets but incomplete message. Never treat a partial decode as delivery success. Packet IDs reset on addon reload; do not mix screenshots across sessions. The offline lab has no acknowledgement or delivery guarantee.

## 4. Opt-in experiments after the synthetic test

- `/egp chat self`: listen ONLY for incoming in-game whispers whose sender matches your own character. Send yourself `EGTEST hello`, then Unicode text, then a longer message. No other players' chat, public channels or Battle.net whispers are collected. `/egp chat off` stops listening and clears queued data. Synthetic generation is disabled when enabling this test.
- `/egp quests`: take one noncombat quest-log snapshot, using quest IDs and numeric objective counts. No external data provider, quest text or automatic quest monitoring. Unsupported or restricted values are omitted. This can produce multiple frames; don't expect one screenshot to contain the full quest log. API restriction errors stop the sample safely.
- `/egp rate 1`, `2`, `5`, or `10`: choose publication frequency. A manual screenshot does not measure a capture rate or establish throughput.
- `/egp status`: prints queue depth, publication count, dropped records, rejected samples, combat skips and retained records. A published frame means drawn by the addon, not successfully captured.
- `/egp clear`: clear retained records in memory. `/reload` persists the clearing.

Only 500 records are retained; each payload is capped at 4096 UTF-8 bytes. Queue capacity is 256 packet transmissions, including repeats. On overflow the entire new record is dropped, counted and not recorded. Synthetic generation can outrun a slow rate when a record needs multiple fragments. The queue is deliberately bounded.

## 5. Compare SavedVariables

The addon keeps accepted synthetic/self-whisper/quest records in ElunesGazePoCDB. It cannot request an immediate arbitrary file write. After `/reload` or a clean logout, inspect:

`_retail_/WTF/Account/<account>/SavedVariables/ElunesGazePoC.lua`

Compare record text with decoded output. This tests batch export separately from pixels; timestamps on disk should not be interpreted as a live stream. Chat samples are private data: avoid committing or sharing this file. `/egp clear` followed by `/reload` clears the active file, but WoW backups or copied files may retain older data.

This addon does not enable or toggle WoW's global chat logger. A separate manual `/chatlog` latency experiment can be considered later without changing an existing logging preference silently.

## Protocol v1 and keystone

Each 4x4 solid RGB cell carries 3 bits, MSB first: black=0, blue=1, green=2, cyan=3, red=4, magenta=5, yellow=6, white=7. There are 256 cells in either layout. Four upper-right cells form a fixed 8x8-pixel keystone:

```text
white   magenta
cyan    yellow
```

Read all OTHER cells in row-major order, from the top left. Their 756 bits hold 94 bytes plus four zero padding bits. Twelve header bytes leave 82 payload bytes per frame. Header: ASCII EG (2), version (1), kind (1), record ID (little-endian uint16), fragment index (1-based byte), fragment count (byte), payload length (byte), reserved zero (byte), Fletcher-16 (little-endian uint16). Checksum input is the first 10 header bytes followed by payload, excluding checksum and zero padding. Types: 0 idle, 1 synthetic, 2 self-whisper, 3 quest, 4 saved diagnostic (not normally transmitted). UTF-8 JSON payloads may split within a character; decode only after byte reassembly. Record IDs wrap at 65536. Every record is transmitted twice, without acknowledgement.

At 2 Hz, the theoretical payload ceiling is 164 B/s before repetition, or at most 82 unique B/s with two transmissions, excluding idle frames and partial fragments. At 5 Hz those ceilings are 410 and 205 B/s. These replace our earlier optimistic one-byte-per-cell estimates. No claim about reliable real-time chat follows from these figures.

## Validation and sources

See VALIDATION.md for offline test results and their limits. The implementation references Blizzard-shipped UI source mirrored at:
- https://github.com/Gethe/wow-ui-source/blob/live/Interface/AddOns/Blizzard_SharedXML/PixelUtil.lua
- https://github.com/Gethe/wow-ui-source/blob/live/Interface/AddOns/Blizzard_APIDocumentationGenerated/QuestLogDocumentation.lua
- https://github.com/Gethe/wow-ui-source/blob/live/Interface/AddOns/Blizzard_ChatFrameBase/Mainline/ChatFrameOverrides.lua

To reproduce offline tests (optional development dependency): `python -m pip install lupa==2.8`, then `python test_offline.py`. This executes the Lua 5.1 implementation with mocked game APIs. It does not launch WoW.

GPL-3.0-only; see LICENSE. Independent fan project; no process memory reads, injection, input automation, protected/secret extraction, restriction bypass or game commands. Restricted data is omitted. There is no policy approval or current-client compatibility claim.
