import sys, json, importlib.util, subprocess
from pathlib import Path

from lupa.lua51 import LuaRuntime
from PIL import Image
root = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('reader', root / 'read_strip.py')
reader = importlib.util.module_from_spec(spec); spec.loader.exec_module(reader)
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
_frames = {}; _combat = false; _clock = 1000
UIParent = { GetEffectiveScale = function() return 0.8 end }
SlashCmdList = {}
function print(...) end
function InCombatLockdown() return _combat end
function time() return _clock end
function GetPhysicalScreenSize() return 1920, 1080 end
function GetBuildInfo() return 'test', 'test', 'test', 120100 end
function UnitFullName() return 'Tester', 'Realm' end
function issecretvalue(v) return type(v) == 'table' and v.secret == true end
function CreateFrame(kind, name, parent)
    local f = {scripts = {}, registered = {}, textures = {}, shown = false}
    function f:SetScript(event, fun) self.scripts[event] = fun end
    function f:RegisterEvent(event) self.registered[event] = true end
    function f:UnregisterEvent(event) self.registered[event] = nil end
    function f:CreateTexture()
        local t = {}
        function t:SetColorTexture(r,g,b,a) self.rgb = {r,g,b} end
        function t:SetSize(w,h) self.width=w; self.height=h end
        function t:SetPoint(a,b,c,x,y) self.x=x; self.y=y end
        function t:ClearAllPoints() end
        function t:SetSnapToPixelGrid() end
        function t:SetTexelSnappingBias() end
        table.insert(self.textures,t); return t
    end
    function f:SetScale(s) self.scale=s end
    function f:SetSize(w,h) self.width=w; self.height=h end
    function f:SetPoint(a,b,c,x,y) self.x=x; self.y=y end
    function f:GetLeft() return self.x end
    function f:GetBottom() return self.y end
    function f:SetShown(s) self.shown=s end
    function f:Hide() self.shown=false end
    function f:EnableMouse(s) self.mouse=s end
    function f:ClearAllPoints() end
    function f:SetFrameStrata() end
    function f:SetAlpha() end
    function f:SetMovable() end
    function f:SetClampedToScreen() end
    function f:RegisterForDrag() end
    function f:StartMoving() end
    function f:StopMovingOrSizing() end
    table.insert(_frames,f); return f
end
C_QuestLog = {
 GetNumQuestLogEntries = function() return 1 end,
 GetInfo = function(i) return {questID = 12345} end,
 GetQuestObjectives = function(id) return {{numFulfilled=1,numRequired=8}} end
}
''')
ns=lua.table()
for name in ['Protocol.lua','Main.lua']:
    lua.execute((root/'ElunesGazePoC'/name).read_text(), 'ElunesGazePoC', ns)
g=lua.globals(); strip, events = g._frames[1],g._frames[2]
events.scripts.OnEvent(events,'ADDON_LOADED','ElunesGazePoC')
assert not strip.shown and not events.registered['CHAT_MSG_WHISPER']
command = g.SlashCmdList.ELUNESGAZEPOC
def tick(dt=.51): events.scripts.OnUpdate(events,dt)
def picture():
    im=Image.new('RGB',(int(strip.width),int(strip.height)))
    for _,t in strip.textures.items():
        color=tuple(round(t.rgb[i]*255) for i in (1,2,3))
        x,y=int(t.x),int(-t.y)
        im.paste(color,(x,y,x+4,y+4))
    return im
def current(layout='slim'): return reader.decode_at(picture(),0,0,layout)
def text(result): return result['payload'].decode()
command('sample'); tick()
assert json.loads(text(current()))['text']=='Hello from Elunes Gaze'
fixtures=root/'fixtures'; fixtures.mkdir(exist_ok=True)
picture().save(fixtures/'slim.png')
assert abs(strip.scale * .8 * 1080 / 768 - 1) < 1e-9
slim=current()
command('fat'); tick()
assert current('fat')['payload']==slim['payload']
picture().save(fixtures/'fat.png')
canvas=Image.new('RGB',(640,480),(37,45,60)); canvas.paste(picture(),(123,207))
canvas.save(fixtures/'fat-in-image.png')
found=reader.find_strip(canvas)
assert (found['x'],found['y'],found['layout'])==(123,207,'fat')
bad=picture(); bad.paste((255,255,255),(0,0,4,4))
try: reader.decode_at(bad,0,0,'fat'); raise AssertionError('corruption accepted')
except ValueError: pass
# Palette drift: primary channels shifted to 25/230, still readable.
noisy=picture().point(lambda v: 230 if v>128 else 25)
assert reader.find_strip(noisy)['payload']==slim['payload']
command('off'); assert not strip.shown
command('slim'); command('chat self')
assert events.registered['CHAT_MSG_WHISPER']
events.scripts.OnEvent(events,'CHAT_MSG_WHISPER','private other text','Other-Realm',None,None,None,'')
assert len(g.ElunesGazePoCDB.records)==1
long='你好 🌙 '+('x'*200)
events.scripts.OnEvent(events,'CHAT_MSG_WHISPER',long,'Tester-Realm',None,None,None,'')
parts={}
for _ in range(6):
    tick(); r=current(); parts[r['part']]=r['payload']
assert json.loads(b''.join(parts[i] for i in sorted(parts)).decode())['text']==long
# Secret chat values are never serialized.
n=len(g.ElunesGazePoCDB.records)
events.scripts.OnEvent(events,'CHAT_MSG_WHISPER',lua.table_from({'secret':True}),'Tester',None,None,None,'')
assert len(g.ElunesGazePoCDB.records)==n
command('quests'); tick()
assert json.loads(text(current()))=={'quest':12345,'objectives':[{'i':1,'have':1,'need':8}]}
# Combat immediately hides and clears pending frames, including manual commands.
g._combat=True; events.scripts.OnEvent(events,'PLAYER_REGEN_DISABLED')
assert not strip.shown
n=len(g.ElunesGazePoCDB.records); command('quests'); tick()
assert len(g.ElunesGazePoCDB.records)==n
g._combat=False; events.scripts.OnEvent(events,'PLAYER_REGEN_ENABLED')
assert json.loads(text(current()))=={'type':'idle'}
command('clear'); assert len(g.ElunesGazePoCDB.records)==0
# Queue is bounded; dropped records do not create partial records.
command('chat self')
for _ in range(300):
    events.scripts.OnEvent(events,'CHAT_MSG_WHISPER','hello','Tester',None,None,None,'')
assert len(g.ElunesGazePoCDB.records)==128
command('off'); assert not events.registered['CHAT_MSG_WHISPER']
# Independent roundtrip across every possible byte, including zero and 255.
binary=bytes(range(256))
lua_bytes=LuaRuntime(unpack_returned_tuples=True,encoding=None)
nsb=lua_bytes.table(); lua_bytes.execute((root/'ElunesGazePoC/Protocol.lua').read_bytes(), b'test', nsb)
packets=nsb[b'Protocol'][b'Parts'](1,65535,binary)
recovered=[]
for _,packet in packets.items():
    codes=nsb[b'Protocol'][b'Encode'](packet)
    im=Image.new('RGB',(16,256)); j=1
    for i in range(256):
        if i in reader.markers(4): value=reader.markers(4)[i]
        else: value=int(codes[j]); j+=1
        im.paste(reader.PALETTE[value],((i%4)*4,(i//4)*4,(i%4)*4+4,(i//4)*4+4))
    recovered.append(reader.decode_at(im,0,0,'slim')['payload'])
assert b''.join(recovered)==binary
for filename in ['slim.png','fat.png','fat-in-image.png']:
    result=subprocess.run([sys.executable,str(root/'read_strip.py'),str(fixtures/filename)],capture_output=True,text=True)
    assert result.returncode==0,(filename,result.stderr)
    print(result.stdout.strip())
print('PASS: Lua addon execution under mocked WoW APIs, RGB image decoding, both layouts, auto-alignment, corruption rejection, palette drift, Unicode fragmentation, quest snapshot, private/secret filtering, combat suspension, bounded queue, all-byte codec roundtrip, CLI fixtures.')

