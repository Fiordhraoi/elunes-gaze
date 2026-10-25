-- SPDX-License-Identifier: GPL-3.0-only
local _, ns = ...
local P = { VERSION = 1, BYTES = 94, PAYLOAD = 82 }
ns.Protocol = P

local function word(n) return string.char(n % 256, math.floor(n / 256) % 256) end
local function checksum(s)
    local a, b = 0, 0
    for i = 1, #s do a = (a + s:byte(i)) % 255; b = (b + a) % 255 end
    return b * 256 + a
end

function P.Packet(kind, id, part, count, payload)
    assert(#payload <= P.PAYLOAD and part >= 1 and part <= count and count <= 255)
    local head = "EG" .. string.char(1, kind) .. word(id)
        .. string.char(part, count, #payload, 0)
    return head .. word(checksum(head .. payload)) .. payload
        .. string.rep("\0", P.PAYLOAD - #payload)
end

function P.Encode(packet)
    assert(#packet == P.BYTES)
    local cells, accumulator, bits = {}, 0, 0
    for i = 1, #packet do
        accumulator = accumulator * 256 + packet:byte(i); bits = bits + 8
        while bits >= 3 do
            bits = bits - 3
            cells[#cells + 1] = math.floor(accumulator / 2 ^ bits) % 8
        end
        accumulator = accumulator % 2 ^ bits
    end
    if bits > 0 then cells[#cells + 1] = accumulator * 2 ^ (3 - bits) end
    while #cells < 252 do cells[#cells + 1] = 0 end
    return cells
end

function P.Parts(kind, id, text)
    assert(#text <= 4096)
    local packets, count = {}, math.max(1, math.ceil(#text / P.PAYLOAD))
    for part = 1, count do
        packets[part] = P.Packet(kind, id, part, count,
            text:sub((part - 1) * P.PAYLOAD + 1, part * P.PAYLOAD))
    end
    return packets
end
