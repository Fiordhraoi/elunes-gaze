# Offline validation - 2026-10-25

Passed using Lua executed through Lupa 2.8 with mocked WoW APIs, Pillow-rendered screenshots from the addon's actual texture colors, and the delivered Python reader:

- Lua source loads and initializes with output/chat OFF.
- Both Slim/Fat produce the expected sample text with checksum OK.
- Keystone auto-location finds Fat at x=123, y=207 in a larger image.
- A damaged data cell is rejected.
- Channel values drifted from 0/255 to 25/230 still decode.
- All 256 byte values round-trip through Lua packetization, color cells, an image, and Python decoding.
- Multi-frame UTF-8 self-whisper messages reassemble without character corruption.
- Other-player whispers and simulated secret values are omitted.
- A mocked quest objective exports quest 12345 and progress 1/8.
- Combat hides the strip, clears pending packets, and prevents quest sampling.
- Queue overflow drops whole records at its configured bound.
- Disabling the addon stream unregisters self-whisper sampling.
- The reader CLI returns success for all three fixture images.

Not tested: actual WoW execution, real API restrictions, client interface compatibility, real UI scale/drag alignment, screenshots from Windows/Linux/SteamOS, HDR, JPEG, OS capture permissions, live capture rate, dropped-frame probability, background-window behavior, real chat logging flush latency, policy approval.

Fixtures are generated images, not screenshots from WoW. They validate the codec and reader together; they do not establish that a live captured strip will have the same colors or geometry. First success criterion in game: a native PNG screenshot produces checksum OK and the expected sample/idle text in both layouts, at your chosen UI scale.
