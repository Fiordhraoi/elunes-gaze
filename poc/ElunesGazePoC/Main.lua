-- SPDX-License-Identifier: GPL-3.0-only
local addon, ns = ...
local P = ns.Protocol
local frame = CreateFrame("Frame", "ElunesGazePoCStrip", UIParent)
local events = CreateFrame("Frame")
local cells, queue, db = {}, {}, nil
local layout, hz, enabled, synthetic, selfChat = "slim", 2, false, false, false
local messageID, syntheticID, elapsed, syntheticElapsed = 0, 0, 0, 0
local x, y, unlocked = 8, 8, false
local dropped, rejected, published, combatSkipped = 0, 0, 0, 0
local function say(s) print("|cffb090ffElune's Gaze:|r " .. s) end
local function ordinary(v)
    return not (issecretvalue and issecretvalue(v))
end
local function safeString(v)
    return ordinary(v) and type(v) == "string" and v or nil
end
local function safeNumber(v)
    return ordinary(v) and type(v) == "number" and v == v and v >= 0 and v <= 2147483647 and v or nil
end
local function quoted(s)
    return '"' .. s:gsub('[%z\1-\31\\"]', function(c)
        return string.format("\\u%04x", c:byte())
    end) .. '"'
end
local function record(kind, text)
    if not db then return end
    db.records[#db.records + 1] = { time = time(), kind = kind, text = text }
    if #db.records > 500 then table.remove(db.records, 1) end
end
local function enqueue(kind, text)
    if InCombatLockdown() then combatSkipped = combatSkipped + 1; return end
    if #text > 4096 then rejected = rejected + 1; return end
    local nextID = (messageID + 1) % 65536
    local packets = P.Parts(kind, nextID, text)
    if #queue + #packets * 2 > 256 then dropped = dropped + 1; return end
    messageID = nextID
    -- Repeat a complete record twice; no acknowledgement channel is assumed.
    for repeatIndex = 1, 2 do
        for _, packet in ipairs(packets) do queue[#queue + 1] = packet end
    end
    record(kind, text)
end
local function setColor(t, value)
    t:SetColorTexture(math.floor(value / 4) % 2, math.floor(value / 2) % 2, value % 2, 1)
end
local function arrange()
    local width, height = 16, 256
    if layout == "fat" then width, height = 32, 128 end
    local _, physicalHeight = GetPhysicalScreenSize()
    -- Convert physical pixels to the client's base UI coordinate space.
    frame:SetScale((768 / physicalHeight) / UIParent:GetEffectiveScale())
    frame:SetSize(width, height)
    frame:ClearAllPoints(); frame:SetPoint("BOTTOMLEFT", UIParent, "BOTTOMLEFT", x, y)
    local columns = width / 4
    for index = 1, 256 do
        local t = cells[index]
        if not t then
            t = frame:CreateTexture(nil, "OVERLAY"); cells[index] = t
            if t.SetSnapToPixelGrid then t:SetSnapToPixelGrid(false); t:SetTexelSnappingBias(0) end
        end
        t:ClearAllPoints(); t:SetSize(4, 4)
        t:SetPoint("TOPLEFT", frame, "TOPLEFT", ((index - 1) % columns) * 4,
            -math.floor((index - 1) / columns) * 4)
        setColor(t, 0)
    end
    frame:EnableMouse(unlocked)
    frame:SetShown(enabled and not InCombatLockdown())
end
local function draw(packet)
    local data, n = P.Encode(packet), 1
    local columns = layout == "fat" and 8 or 4
    -- Keystone at upper right: white, magenta / cyan, yellow.
    local markers = { [columns - 1] = 7, [columns] = 5,
        [2 * columns - 1] = 3, [2 * columns] = 6 }
    for i = 1, 256 do
        if markers[i] then setColor(cells[i], markers[i])
        else setColor(cells[i], data[n]); n = n + 1 end
    end
end
local function idle()
    draw(P.Packet(0, 0, 1, 1, '{"type":"idle"}'))
end
frame:SetFrameStrata("HIGH"); frame:SetAlpha(1)
frame:SetMovable(true); frame:SetClampedToScreen(true); frame:RegisterForDrag("LeftButton")
frame:SetScript("OnDragStart", function() if unlocked and not InCombatLockdown() then frame:StartMoving() end end)
frame:SetScript("OnDragStop", function()
    frame:StopMovingOrSizing()
    x = math.floor(frame:GetLeft() + 0.5); y = math.floor(frame:GetBottom() + 0.5)
    db.x, db.y = x, y; arrange(); idle()
end)
frame:Hide()

local function quests()
    if InCombatLockdown() then say("Quest sampling is paused in combat."); return end
    if not C_QuestLog or not C_QuestLog.GetQuestObjectives then say("Quest APIs unavailable."); return end
    local ok, err = pcall(function()
        local total = C_QuestLog.GetNumQuestLogEntries()
        if not safeNumber(total) then return end
        local count = 0
        for i = 1, math.min(total, 200) do
            local info = C_QuestLog.GetInfo(i)
            if info and ordinary(info) then
                local id = safeNumber(info.questID)
                if id and id > 0 then
                    local objectives = C_QuestLog.GetQuestObjectives(id)
                    local pieces = {}
                    if objectives and ordinary(objectives) then
                        for j, objective in ipairs(objectives) do
                            if j > 32 then break end
                            if ordinary(objective) then
                                local have, need = safeNumber(objective.numFulfilled), safeNumber(objective.numRequired)
                                if have and need then
                                    pieces[#pieces + 1] = string.format('{"i":%d,"have":%d,"need":%d}', j, have, need)
                                end
                            end
                        end
                    end
                    enqueue(3, string.format('{"quest":%d,"objectives":[%s]}', id, table.concat(pieces, ",")))
                    count = count + 1
                end
            end
        end
        record(4, string.format('{"questSnapshotEntries":%d}', count))
        say("Sampled " .. count .. " quest entries; status reports any queue drops.")
    end)
    if not ok then rejected = rejected + 1; say("Quest sample stopped: an API was unavailable or restricted.") end
end

events:RegisterEvent("ADDON_LOADED")
events:RegisterEvent("PLAYER_REGEN_DISABLED"); events:RegisterEvent("PLAYER_REGEN_ENABLED")
events:RegisterEvent("DISPLAY_SIZE_CHANGED"); events:RegisterEvent("UI_SCALE_CHANGED")
events:SetScript("OnEvent", function(_, event, ...)
    if event == "ADDON_LOADED" then
        if ... ~= addon then return end
        ElunesGazePoCDB = ElunesGazePoCDB or {}
        db = ElunesGazePoCDB; db.records = db.records or {}; db.schema = 1
        layout = db.layout == "fat" and "fat" or "slim"
        x, y = tonumber(db.x) or 8, tonumber(db.y) or 8
        local version, build, _, interface = GetBuildInfo()
        db.client = { version = version, build = build, interface = interface }
        arrange(); idle()
        say("Lab loaded. Output and chat capture are OFF. /egp help")
    elseif not db then return
    elseif event == "PLAYER_REGEN_DISABLED" then
        queue = {}; frame:StopMovingOrSizing(); frame:Hide()
    elseif event == "PLAYER_REGEN_ENABLED" then
        elapsed, syntheticElapsed = 0, 0; arrange(); idle()
    elseif event == "DISPLAY_SIZE_CHANGED" or event == "UI_SCALE_CHANGED" then
        if not InCombatLockdown() then arrange(); idle() end
    elseif selfChat and not InCombatLockdown() and event == "CHAT_MSG_WHISPER" then
        local message, sender, _, _, _, flag = ...
        message, sender, flag = safeString(message), safeString(sender), safeString(flag)
        if not message or not sender or flag == "GM" then rejected = rejected + 1; return end
        local mine, realm = UnitFullName("player")
        mine, realm = safeString(mine), safeString(realm)
        if not mine then return end
        local full = realm and (mine .. "-" .. realm:gsub("%s", "")) or mine
        if sender ~= mine and sender ~= full then return end
        enqueue(2, '{"type":"self-whisper","text":' .. quoted(message) .. '}')
    end
end)

events:SetScript("OnUpdate", function(_, delta)
    if not db or not enabled or InCombatLockdown() then return end
    if synthetic then
        syntheticElapsed = syntheticElapsed + delta
        if syntheticElapsed >= 1 then
            syntheticElapsed = 0; syntheticID = syntheticID + 1
            enqueue(1, string.format('{"type":"synthetic","n":%d,"text":"Elunes Gaze test"}', syntheticID))
        end
    end
    elapsed = elapsed + delta
    if elapsed >= 1 / hz then
        elapsed = 0
        if #queue > 0 then draw(table.remove(queue, 1)); published = published + 1
        else idle() end
    end
end)

SLASH_ELUNESGAZEPOC1 = "/egp"
SlashCmdList.ELUNESGAZEPOC = function(input)
    if not db then return end
    local command, argument = input:match("^(%S*)%s*(.-)%s*$")
    command = command:lower()
    if command == "off" then
        enabled, synthetic, selfChat = false, false, false; queue = {}
        events:UnregisterEvent("CHAT_MSG_WHISPER"); frame:Hide(); say("Output and chat capture off.")
    elseif command == "status" then
        say(string.format("%s, %s, %d Hz; queued %d frames, published %d, dropped %d records, rejected %d, combat skipped %d; saved %d records.",
            enabled and "ON" or "OFF", layout, hz, #queue, published, dropped, rejected, combatSkipped, #db.records))
    elseif InCombatLockdown() then say("Wait until you are out of combat.")
    elseif command == "on" or command == "test" then
        enabled = true; synthetic = command == "test"; arrange(); idle()
        if synthetic then say("Synthetic stream on; no game data is sampled.") end
    elseif command == "slim" or command == "fat" then
        layout = command; db.layout = layout; arrange(); idle()
    elseif command == "rate" and (argument == "1" or argument == "2" or argument == "5" or argument == "10") then
        hz = tonumber(argument); say("Publication rate " .. hz .. " Hz.")
    elseif command == "unlock" or command == "lock" then
        unlocked = command == "unlock"; arrange(); idle(); say(unlocked and "Drag the strip, then /egp lock." or "Position locked.")
    elseif command == "reset" then x, y = 8, 8; db.x, db.y = x, y; arrange(); idle()
    elseif command == "sample" then
        enabled = true; synthetic = false; arrange()
        enqueue(1, '{"type":"sample","text":"Hello from Elunes Gaze"}')
    elseif command == "quests" then
        enabled = true; synthetic = false; arrange(); quests()
    elseif command == "chat" and argument == "self" then
        enabled, synthetic, selfChat = true, false, true; arrange()
        events:RegisterEvent("CHAT_MSG_WHISPER"); say("Only whispers from your own character are sampled. /egp chat off stops it.")
    elseif command == "chat" and argument == "off" then
        selfChat = false; queue = {}; events:UnregisterEvent("CHAT_MSG_WHISPER"); idle()
    elseif command == "clear" then
        db.records = {}; queue = {}; idle(); say("Local history cleared in memory. /reload to persist.")
    else
        say("/egp sample | test | on | off | slim | fat | rate 1/2/5/10 | unlock | lock | reset | status")
        say("/egp quests (one snapshot) | chat self | chat off | clear. Nothing writes SavedVariables immediately; /reload saves.")
    end
end
