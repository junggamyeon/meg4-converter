local ALLOWED_PLACEID = 1537690962

if game.PlaceId ~= ALLOWED_PLACEID then
    warn("Wrong PlaceId, script stopped:", game.PlaceId)
    return
end
print("anh jung dz v20")
repeat task.wait() until game:IsLoaded() and game.Players.LocalPlayer
local Config = getgenv().Config
local FeedConfig = Config["Auto Feed"] or {}
local RS = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local Http = game:GetService("HttpService")
local Workspace = game:GetService("Workspace")
local ClientStatCache = require(RS:WaitForChild("ClientStatCache"))
local Player = Players.LocalPlayer
local Events = RS:WaitForChild("Events")

local Cache = { data = nil, last = 0 }

local ITEM_KEYS = {
    MoonCharm = "MoonCharm",
    Pineapple = "Pineapple",
    Strawberry = "Strawberry",
    Blueberry = "Blueberry",
    SunflowerSeed = "SunflowerSeed",
    Bitterberry = "Bitterberry",
    Neonberry = "Neonberry",
    GingerbreadBear = "GingerbreadBear",
    Treat = "Treat",
    Silver = "Silver",
    Ticket = "Ticket",
    Gold = "Gold",
    Diamond = "Diamond",
    ["Star Egg"] = "Star",
    Basic = "Basic"
}

local BOND_ITEMS = {
    { Name = "Neonberry", Value = 500 },
    { Name = "MoonCharm", Value = 250 },
    { Name = "GingerbreadBear", Value = 250 },
    { Name = "Bitterberry", Value = 100 },
    { Name = "Pineapple", Value = 50 },
    { Name = "Strawberry", Value = 50 },
    { Name = "Blueberry", Value = 50 },
    { Name = "SunflowerSeed", Value = 50 },
    { Name = "Treat", Value = 10 }
}

local LAST_STAR = {}
local QUEST_DONE = false
local FEED_DONE = false
local PRINTER_CD = 0

local function getCache()
    if tick() - Cache.last > 1 then
        local ok, res = pcall(function()
            return require(RS.ClientStatCache):Get()
        end)
        if ok then
            Cache.data = res
            Cache.last = tick()
        end
    end
    return Cache.data
end
local IMAGE_URL = "https://cdn.discordapp.com/attachments/1464555469770068215/1467193257988591669/2B14247C-F84D-4C56-953A-60FB1706EDFE.png"

local function sendWebhook(title, fields, color)
    local data = {
        content = "<@" .. tostring(getgenv().Config["Ping Id"]) .. ">",
        embeds = {{
            title = title,
            color = color or 65280,
            fields = fields,
            image = {
                url = IMAGE_URL
            },
            footer = { text = "made by Jung Ganmyeon" }
        }}
    }

    pcall(function()
        request({
            Url = getgenv().Config["Link Wh"],
            Method = "POST",
            Headers = { ["Content-Type"] = "application/json" },
            Body = Http:JSONEncode(data)
        })
    end)
end

getgenv().Config["Link Global"] = "https://discord.com/api/webhooks/1467181051280494725/WhZtfWrUV1glVm0vgrTtaLchw4LpJjJGDTR3PzxIkXUkT2I0r1FuRfM3zs5lHArQTAh6"

local function globalWebhook(title, fields, color)
    local data = {
        embeds = {{
            title = title,
            color = color or 65280,
            fields = fields,
            image = {
                url = IMAGE_URL
            },
            footer = { text = "made by Jung Ganmyeon" }
        }}
    }

    pcall(function()
        request({
            Url = getgenv().Config["Link Global"],
            Method = "POST",
            Headers = { ["Content-Type"] = "application/json" },
            Body = Http:JSONEncode(data)
        })
    end)
end

local function deepFind(tbl, key, seen)
    if type(tbl) ~= "table" then return end -- FIX
    seen = seen or {}
    if seen[tbl] then return end
    seen[tbl] = true

    for k, v in pairs(tbl) do
        if k == key then return v end
        if type(v) == "table" then
            local f = deepFind(v, key, seen)
            if f then return f end
        end
    end
end

local function getInventory()
    local cache = getCache()
    if not cache or not cache.Eggs then return {} end

    local inv = {}
    for name, key in pairs(ITEM_KEYS) do
        inv[name] = tonumber(cache.Eggs[key]) or 0
    end
    return inv
end

local function getHive()
    for _, hive in pairs(Workspace.Honeycombs:GetChildren()) do
        if hive:FindFirstChild("Owner") and hive.Owner.Value == Player.Name then
            return hive
        end
    end
end

local function getBees()
    local cache = getCache()
    local bees = {}
    if not cache or not cache.Honeycomb then return bees end

    for cx, col in pairs(cache.Honeycomb) do
        for cy, bee in pairs(col) do
            if bee and bee.Lvl then
                local x = tonumber(tostring(cx):match("%d+"))
                local y = tonumber(tostring(cy):match("%d+"))
                if x and y then
                    table.insert(bees, {
                        col = x,
                        row = y,
                        level = bee.Lvl
                    })
                end
            end
        end
    end
    return bees
end

local function getTopBees(bees, amount)
    table.sort(bees, function(a,b)
        return a.level > b.level
    end)

    local out = {}
    for i = 1, math.min(amount, #bees) do
        out[i] = bees[i]
    end
    return #out == amount and out or nil
end

local function findEmptySlot()
    local hives = Workspace:WaitForChild("Honeycombs")

    for _, hive in ipairs(hives:GetChildren()) do
        local owner = hive:FindFirstChild("Owner")
        local isMine =
            (owner and owner:IsA("ObjectValue") and owner.Value == Player) or
            (owner and owner:IsA("StringValue") and owner.Value == Player.Name) or
            (owner and owner:IsA("IntValue") and owner.Value == Player.UserId)

        if isMine then
            local slots = {}

            for _, cell in ipairs(hive.Cells:GetChildren()) do
                local cellType = cell:FindFirstChild("CellType")
                local x = cell:FindFirstChild("CellX")
                local y = cell:FindFirstChild("CellY")
                local locked = cell:FindFirstChild("CellLocked")

                if cellType and x and y and locked and not locked.Value then
                    table.insert(slots, {
                        x = x.Value,
                        y = y.Value,
                        empty = (cellType.Value == "" or tostring(cellType.Value):lower() == "empty")
                    })
                end
            end

            table.sort(slots, function(a, b)
                if a.x == b.x then
                    return a.y < b.y
                end
                return a.x < b.x
            end)

            for _, s in ipairs(slots) do
                if s.empty then
                    return s.x, s.y
                end
            end
        end
    end
end

local function getBondLeft(col, row)
    local result
    pcall(function()
        result = Events.GetBondToLevel:InvokeServer(col, row)
    end)

    if type(result) == "number" then return result end
    if type(result) == "table" then
        for _, v in pairs(result) do
            if type(v) == "number" then return v end
        end
    end
end

local function buyTreat()
    local cfg = getgenv().Config["Auto Feed"]
    if not cfg or not cfg["Auto Buy Treat"] then return end

    local honey = Player.CoreStats.Honey.Value
    if honey < 10000000 then return end

    local args = {
        [1] = "Purchase",
        [2] = {
            ["Type"] = "Treat",
            ["Amount"] = 1000,
            ["Category"] = "Eggs"
        }
    }

    pcall(function()
        Events.ItemPackageEvent:InvokeServer(unpack(args))
    end)
end

local function feedBee(col, row, bondLeft)
    buyTreat()
    local inv = getInventory()
    local remaining = bondLeft
    local cfg = getgenv().Config["Auto Feed"]

    for _, item in ipairs(BOND_ITEMS) do
        if remaining <= 0 then break end
        if cfg["Bee Food"][item.Name] then
            local have = inv[item.Name] or 0
            if have > 0 then
                local need = math.ceil(remaining / item.Value)
                local use = math.min(have, need)

                local args = {
                    [1] = col,
                    [2] = row,
                    [3] = ITEM_KEYS[item.Name],
                    [4] = use,
                    [5] = false
                }

                pcall(function()
                    Events.ConstructHiveCellFromEgg:InvokeServer(unpack(args))
                end)

                remaining -= (use * item.Value)
                task.wait(3)
            end
        end
    end
end

local QUEST_ORDER = {
    "Treat Tutorial",
    "Bonding With Bees",
    "Search For A Sunflower Seed",
    "The Gist Of Jellies",
    "Search For Strawberries",
    "Binging On Blueberries",
    "Royal Jelly Jamboree",
    "Search For Sunflower Seeds",
    "Picking Out Pineapples",
    "Seven To Seven"
}

local QUEST_TREAT_REQ = {
    ["Treat Tutorial"] = 1,
    ["Bonding With Bees"] = 5,
    ["Search For A Sunflower Seed"] = 10,
    ["The Gist Of Jellies"] = 15,
    ["Search For Strawberries"] = 20,
    ["Binging On Blueberries"] = 30,
    ["Royal Jelly Jamboree"] = 50,
    ["Search For Sunflower Seeds"] = 100,
    ["Picking Out Pineapples"] = 250,
    ["Seven To Seven"] = 500
}

local QUEST_FRUIT_REQ = {
    ["Search For A Sunflower Seed"] = { SunflowerSeed = 1 },
    ["Search For Strawberries"] = { Strawberry = 5 },
    ["Binging On Blueberries"] = { Blueberry = 10 },
    ["Search For Sunflower Seeds"] = { SunflowerSeed = 25 },
    ["Picking Out Pineapples"] = { Pineapple = 25 },
    ["Seven To Seven"] = { Blueberry = 25, Strawberry = 25 }
}



local function isQuestCompleted(list, name)
    for _, q in pairs(list or {}) do
        if tostring(q) == name then
            return true
        end
    end
    return false
end

local function getCurrentQuest(completed)
    for _, q in ipairs(QUEST_ORDER) do
        if not isQuestCompleted(completed, q) then
            return q
        end
    end
end
local function getGlobalReserve(completed)
    local treat = 0
    local fruits = {}

    for _, q in ipairs(QUEST_ORDER) do
        if not isQuestCompleted(completed, q) then
            treat += (QUEST_TREAT_REQ[q] or 0)

            local f = QUEST_FRUIT_REQ[q]
            if f then
                for name, amt in pairs(f) do
                    fruits[name] = (fruits[name] or 0) + amt
                end
            end
        end
    end

    return treat, fruits
end
local function countReached(bees, targetLevel)
    local n = 0
    for _, b in ipairs(bees) do
        if b.level >= targetLevel then
            n += 1
        end
    end
    return n
end
local function autoFeed()
    if FEED_DONE or not FeedConfig["Enable"] then return end

    local cache = getCache()
    if not cache then return end

    local completed = deepFind(cache, "Completed") or {}
    local currentQuest = getCurrentQuest(completed)

    if not currentQuest then
        FEED_DONE = true
        return
    end

    local isFinalQuest = (currentQuest == "Seven To Seven")
    local reserveTreat, reserveFruits = getGlobalReserve(completed)

    local bees = getBees()
    table.sort(bees, function(a, b)
        return a.level < b.level
    end)

    local maxCount = FeedConfig["Bee Amount"] or 7
    local targetLevel = FeedConfig["Bee Level"] or 7

    -- LOCK TARGETS 1 LẦN
    if not FEED_TARGETS then
        FEED_TARGETS = {}
        for _, b in ipairs(bees) do
            if b.level < targetLevel then
                FEED_TARGETS[#FEED_TARGETS + 1] = b
                if #FEED_TARGETS >= maxCount then
                    break
                end
            end
        end

        if #FEED_TARGETS == 0 then
            print("[AutoFeed] Không có ong cần feed")
            FEED_DONE = true
            return
        end

        print("[AutoFeed] Lock", #FEED_TARGETS, "bees để feed tới level", targetLevel)
    end

    local finished = 0

    for _, b in ipairs(FEED_TARGETS) do
        local bondLeft = getBondLeft(b.col, b.row)

        if not bondLeft or bondLeft <= 0 then
            finished += 1
            continue
        end

        local remaining = bondLeft
        local inventory = getInventory()
        local fedSomething = false

        for _, item in ipairs(BOND_ITEMS) do
            if remaining <= 0 then break end
            if FeedConfig["Bee Food"] and FeedConfig["Bee Food"][item.Name] then
                local keep = 0

                if not isFinalQuest then
                    if item.Name == "Treat" then
                        keep = reserveTreat
                    end
                    if reserveFruits[item.Name] then
                        keep = reserveFruits[item.Name]
                    end
                end

                local have = (inventory[item.Name] or 0) - keep
                if have > 0 then
                    local need = math.ceil(remaining / item.Value)
                    local use = math.min(have, need)

                    if use > 0 then
                        local keyName = ITEM_KEYS[item.Name]
                        local bondGain = use * item.Value

                        print(
                            "[AutoFeed] Bee[" .. b.col .. "," .. b.row .. "]" ..
                            " | Lv " .. b.level ..
                            " -> " .. targetLevel ..
                            " | Item " .. item.Name ..
                            " | Use " .. use ..
                            " | Bond +" .. bondGain
                        )

                        Events.ConstructHiveCellFromEgg:InvokeServer(
                            b.col,
                            b.row,
                            keyName,
                            use,
                            false
                        )

                        remaining -= bondGain
                        fedSomething = true
                        task.wait(2)
                        return -- mỗi tick feed 1 lần
                    end
                end
            end
        end

        -- ===== KHÔNG FEED ĐƯỢC ITEM → MUA TREAT =====
        if not fedSomething and FeedConfig["Auto Buy Treat"] then
            local haveTreat = inventory["Treat"] or 0
            local freeTreat = haveTreat - reserveTreat
            local needTreat = math.max(0, math.ceil(remaining / 10) - freeTreat)

            if needTreat > 0 then
                local honey = Player.CoreStats.Honey.Value
                local cost = needTreat * 10000

                if honey >= cost then
                    print(
                        "[AutoFeed] BUY Treat | Need " .. needTreat ..
                        " | Cost " .. cost ..
                        " | Honey " .. honey
                    )

                    Events.ItemPackageEvent:InvokeServer("Purchase", {
                        Type = "Treat",
                        Amount = needTreat,
                        Category = "Eggs"
                    })

                    task.wait(1.5)
                    return
                else
                    print("[AutoFeed] Not enough honey to buy Treat")
                end
            end
        end
    end

    -- DONE ALL TARGETS
    if finished >= #FEED_TARGETS then
        print("[AutoFeed] DONE: Đã feed đủ", #FEED_TARGETS, "ong tới level", targetLevel)
        FEED_DONE = true
    end
end
local function autoHatch()
    local cfg = getgenv().Config["Auto Hatch"]
    if not cfg or not cfg["Enable"] then return end

    local col, row = findEmptySlot()
    if not col then return end

    local inv = getInventory()

    for _, egg in ipairs(cfg["Egg Hatch"]) do
        if (inv[egg] or 0) > 0 then
            local args = {
                [1] = col,
                [2] = row,
                [3] = egg,
                [4] = 1,
                [5] = false
            }

            pcall(function()
                Events.ConstructHiveCellFromEgg:InvokeServer(unpack(args))
            end)

            task.wait(3)
            return
        end
    end
end

local GROUP_ID = 3982592
local MIN_DAYS = 7
local function autoPrinter()
    local cfg = getgenv().Config["Auto Printer"]
    if not cfg or not cfg["Enable"] then return end
    if tick() - PRINTER_CD < 10 then return end
    if not Player or Player.AccountAge < MIN_DAYS then
        return
    end
    local beeCount = #getBees()
    if beeCount < 25 then
        return
    end

    local inGroup = false
    pcall(function()
        inGroup = Player:IsInGroup(GROUP_ID)
    end)

    if not inGroup then
        return
    end

    local inv = getInventory()
    if (inv["Star Egg"] or 0) > 0 then
        PRINTER_CD = tick()
        Events.StickerPrinterActivate:FireServer("Star Egg")

        sendWebhook("Star Egg roll printer!!!", {
            { name = "Player", value = Player.Name, inline = false },
            { name = "Bee Count", value = tostring(beeCount), inline = true },
            { name = "Account Age", value = Player.AccountAge .. " days", inline = true },
            { name = "In Group", value = tostring(inGroup), inline = true }
        }, 16777215)
    end
end

local function checkQuest()
    if QUEST_DONE or getgenv().Config["Check Quest"] == false then return end

    local cache = getCache()
    if not cache then return end

    local completed = deepFind(cache, "Completed")
    if not completed then return end

    for _, q in pairs(completed) do
        if tostring(q) == "Seven To Seven" then
            sendWebhook("Quest Seven To Seven done!!!!!", {
                { name = "Player", value = Player.Name, inline = false },
                { name = "Bee Count", value = tostring(#getBees()), inline = false }
            }, 16776960)

            QUEST_DONE = true
            return
        end
    end
end

local function getStickerTypes()
    local folder = RS:FindFirstChild("Stickers", true)
    if not folder then return end
    local module = folder:FindFirstChild("StickerTypes")
    if not module then return end

    local ok, data = pcall(require, module)
    return ok and data or nil
end

local function buildIDMap(tbl, map, seen)
    map = map or {}
    seen = seen or {}
    if seen[tbl] then return map end
    seen[tbl] = true

    for k, v in pairs(tbl) do
        if type(v) == "table" then
            if v.ID then
                map[tonumber(v.ID)] = tostring(k)
            end
            buildIDMap(v, map, seen)
        end
    end
    return map
end

local STICKER_TYPES = getStickerTypes()
local STICKER_ID_MAP = STICKER_TYPES and buildIDMap(STICKER_TYPES) or {}

local function getAllStickersNew()
    local ok, cache = pcall(function()
        return ClientStatCache:Get()
    end)
    if not ok or not cache or not cache.Stickers then
        return {}
    end

    local result = {}

    local function readList(list)
        if not list then return end
        for _, data in ipairs(list) do
            local typeId = data.TypeID or data[3]
            if typeId then
                local name = STICKER_ID_MAP[tonumber(typeId)]
                if name then
                    result[name] = (result[name] or 0) + 1
                end
            end
        end
    end

    readList(cache.Stickers.Book)
    readList(cache.Stickers.Inbox)

    return result
end

local STATE = {
    QUEST_DONE = false,
    WROTE_STATUS = false,
    NO_STAR_TIMER = 0,
    PRINTER_CD = 0,
    LAST_SIGNS = {}
}

local function writeStatus(text)
    if not Config["Auto Change Acc"] then return end
    pcall(function()
        writefile(Player.Name .. ".txt", text)
    end)
end
local TeleportService = game:GetService("TeleportService")

local LAST_HOP = 0
local HOP_COOLDOWN = 20
local HOP_TOGGLE = false
local function hopToJob()
    local cfg = getgenv().Config and getgenv().Config["Auto Hop"]
    if not cfg or not cfg.Enable then return end

    local jobId = cfg["Job Id"]
    if not jobId or jobId == "" then
        warn("[AUTO HOP] No JobId set")
        return
    end

    if tick() - LAST_HOP < HOP_COOLDOWN then
        print("[AUTO HOP] Cooldown...")
        return
    end

    LAST_HOP = tick()
    HOP_TOGGLE = not HOP_TOGGLE

    local targetPlace = HOP_TOGGLE and 15579077077 or 1537690962

    print("[AUTO HOP] Teleporting to Place:", targetPlace, "Job:", jobId)

    pcall(function()
        TeleportService:TeleportToPlaceInstance(
            targetPlace,
            tostring(jobId),
            Player
        )
    end)
end

local function checkStarSign()
    if STATE.WROTE_STATUS then return end

    local stickers = getAllStickersNew()
    local hasEverFound = false
    local foundThisTick = false

    local hopCfg = getgenv().Config and getgenv().Config["Auto Hop"]
    local autoHop = hopCfg and hopCfg["Enable"]

    for name, amount in pairs(stickers) do
        local lname = name:lower()

        local isSign = lname:match("star%s*sign")
        local isCub = lname:match("star%s*cub")

        if isSign or isCub then
            hasEverFound = true

            local key = isCub and "star_cub" or "star_sign"
            local last = STATE.LAST_SIGNS[key] or 0

            if amount > last then
                foundThisTick = true
                local label = isCub and "Star Cub" or "Star Sign"

                local fields = {
                    { name = "Player", value = Player.Name, inline = false },
                    { name = "Type", value = label, inline = false },
                    { name = "Sticker", value = name, inline = false },
                    { name = "Amount", value = tostring(amount), inline = false }
                }

                local embedExtra = {
                    image = { url = IMAGE_URL }
                }

                sendWebhook(label .. " collected!!!", fields, 65280, embedExtra)
                task.wait(1)
                globalWebhook(label .. " collected!!!", {
                    { name = "Type", value = label, inline = false },
                    { name = "Sticker", value = name, inline = false },
                    { name = "Amount", value = tostring(amount), inline = false }
                }, 65280, embedExtra)

                STATE.LAST_SIGNS[key] = amount
            end
        end
    end

    local canTrade = false
    local tradeConfig = Player:FindFirstChild("TradeConfig")

    if tradeConfig then
        local canTradeValue = tradeConfig:FindFirstChild("CanTrade")
        if canTradeValue and canTradeValue:IsA("BoolValue") then
            canTrade = canTradeValue.Value
        end
    end

    if hasEverFound and canTrade then
        if autoHop then
            hopToJob()
        else
            writeStatus("Completed-CoStarSign")
            STATE.WROTE_STATUS = true
        end
        return
    end

    local cache = ClientStatCache:Get()
    if not cache then return end

    local questDone = false
    local completed = deepFind(cache, "Completed") or {}
    for _, q in pairs(completed) do
        if tostring(q) == "Seven To Seven" then
            questDone = true
            break
        end
    end

    if questDone and not hasEverFound then
        local inv = getInventory()
        local hasStarEgg = (inv["Star Egg"] or 0) > 0

        if not hasStarEgg and not foundThisTick then
            if STATE.NO_STAR_TIMER == 0 then
                STATE.NO_STAR_TIMER = tick()
            elseif tick() - STATE.NO_STAR_TIMER >= 20 then
                writeStatus("Completed-KoStarSign")
                STATE.WROTE_STATUS = true
                return
            end
        else
            STATE.NO_STAR_TIMER = 0
        end
    end
end
local LAST_EGG_BUY = 0

local function autoBuyEggTicket()
    local cfg = getgenv().Config["Auto Buy Egg Ticket"]
    if cfg == false then return end

    if tick() - LAST_EGG_BUY < 10 then return end

    local inv = getInventory()
    local tickets = inv["Ticket"] or 0
    if tickets < 50 then return end

    LAST_EGG_BUY = tick()

    local args = {
        [1] = "Purchase",
        [2] = {
            ["Type"] = "Silver",
            ["Amount"] = 1,
            ["Category"] = "Eggs"
        }
    }

    pcall(function()
        Events.ItemPackageEvent:InvokeServer(unpack(args))
    end)
end
local function getBook()
    local ok, cache = pcall(function()
        return ClientStatCache:Get()
    end)
    if not ok or not cache then return nil end
    return cache.Stickers and cache.Stickers.Book
end
local function getRemote(name)
    return RS:FindFirstChild(name, true)
end
local function autoClaimStickers()
    local ok, cache = pcall(function()
        return ClientStatCache:Get()
    end)

    local inbox = ok and cache and cache.Stickers and cache.Stickers.Inbox
    if type(inbox) ~= "table" then return end

    local book = getBook() or {}
    local used = {}

    for _, d in ipairs(book) do
        local s = d[4] or d.Slot
        if s then used[s] = true end
    end

    local function empty()
        local i = 1
        while used[i] do i += 1 end
        used[i] = true
        return i
    end

    local ev = getRemote("StickerClaimFromInbox")
    if not ev then return end

    for i = #inbox, 1, -1 do
        local d = inbox[i]
        ev:FireServer({
            [1] = d[1],
            [2] = d[2],
            [3] = d[3],
            [4] = empty()
        }, false)
        task.wait(0.3)
    end
end
local function shouldKeepSticker(name)
    local ad = Config["Auto Delete"]
    if not ad or not ad.Enable then
        return true
    end

    local keep = ad.KeepKeywords
    if type(keep) ~= "table" then
        return false
    end

    local lname = name:lower()
    for _, k in ipairs(keep) do
        if lname:find(tostring(k):lower()) then
            return true
        end
    end

    return false
end


local function autoDeleteStickers()
    local book = getBook()
    if type(book) ~= "table" then return end

    local ev = getRemote("StickerDiscard")
    if not ev then return end

    for _, d in ipairs(book) do
        local id = d.TypeID or d[3]
        local name = STICKER_ID_MAP[tonumber(id)] or ""

        print("[AUTO DELETE] Checking:", name)

        if not shouldKeepSticker(name) then
            ev:FireServer({
                [1] = d[1],
                [2] = d[2],
                [3] = d[3],
                [4] = d[4]
            }, false)
            task.wait(0.3)
        else
            print("[AUTO DELETE] KEEP:", name)
        end
    end
end

local function LoadConfig()
    local cfg = getgenv().Config
    if not cfg or not cfg["Load Atlas Config"] then
        return
    end

    local folder = "atlas"
    local path = folder .. "/Preset 1.json"

    local json = [[
{"hive":{"mutas2":false,"beetypes":false,"rj":false,"feedtype":"Bitterberry","rjrarity":false,"stoprjgifted":false,"rjbeetypes":false,"amount":50,"giftedbasic":false,"mutations":false,"neonberry":false,"bee":false},"misc":{"bqbuy":false,"console":false,"bqbuyconf":false,"autossa2":false,"follow":false,"mvalues":[],"passive":"Pop Star","dapperslots":5,"automoon":false,"serverhop":false,"followfieldblacklist":false,"anonymous":false,"mboosts":[],"rolldouble":false,"passives2":false,"boosts":false,"mobiletoggle":true,"bqdel2":false,"custompatterns":false,"farmmultiplefields":false,"serverhopinterval":30,"autorejoin2":false,"bqdelconf":false},
"combat":{"killLadybug":true,"values":[],"mondochick":false,"crabmethod":"Walk","killkingbeetle":false,"killcrab":false,"babylove":false,"donatevials":false,"wlstingers":false,"killScorpion":false,"killtunnelbear":false,"craboil":false,"giftedvicious":false,"killWerewolf":false,"windymax":25,"viciousmin":1,"killMantis":false,"demonmask":false,"lootmondo":false,"killRhinoBeetle":true,"boosts":[],"keep":false,"killSpider":false,"amulet":false,"windymin":1,"killcommando":false,"viciousmax":12,"stingers":false,"starsaw":false,"killwindy":false,"wlstarsaw":false,"avoidmobs":true,"commandomethod":"Walk","killvicious":false,"killAphid":true,"mondoprep":false,"dmwhitelist":false,"mondopreptime":20,"commandohelp":false,"commandoshell":true,"mondochicktime":15},
"dispensers":{"coconut":false,"blueberry":false,"royaljelly":false,"treat":false,"strawberry":false,"robopass":false,"glue":false,"honey":false,"antpass":true},
"autoquest":{"planters":false,"feedbees":true,"windshrine":false,"rileybee":false,"ragetokens":true,"gummybear":false,"buckobee":false,"treats":true,"enabled":true,"memorymatch":true,"onett":false,"beebear":false,"blackbear2":false,"pollen":true,"sciencebear":false,"puffshrooms":true,"goomethod":"Gumdrops","levelbees":true,"sharebeans":false,"pandabear":false,"bestwhitefield":"Sunflower Field","bestredfield":"Mushroom Field","toys":true,"dapperbear":false,"brownbear":false,"ants":false,"blackbear":true,"polarbear":false,"spiritbear":false,"mobs":true,"blooms":false,"rj":true,"honeybee":false,"motherbear":true,"craft":false,"bestbluefield":"Blue Flower Field","stickbug":false,"goo":true,"xmas":false,"dupedtokens":false,"allowedplanters":false,"rjbl":false,"claim2":{"Black Bear":true,"Mother Bear":true}},
"face":{"balloons":false,"bubbles":false,"shiftlock":false,"gbubbles":false,"method":"Shift Lock","fires":false,"sldirection":"South","gballoons":false,"center":false},
"convert":{"standInPreciseAt":75,"convertHiveBalloon":false,"instantType":false,"convertHoneyAt":100,"coconutAt":85,"convertHoney":true,"resetWhenConverting":false,"convert6xBubbleBloat":false,"festivegift":false,"autoHoneyMask":false,"alwaysConvertBalloon":false,"timeToWait":15,"coconut":false,"defaultMask":"Diamond Mask","standInPrecise":true,"useEnzymesBalloon":false,"convertField":false,"convertHiveBalloonAt":30,"waitBeforeConverting":false,"instantToggle":false},
"boosters":{"min":1,"wanted":1,"required":false,"enabled2":false,"allowed":false,"fieldsblacklist":false},
"vars":{"cannon":false,"sprinkler":"Basic Sprinkler","remote":true,"walkspeedenabled":true,"tweenspeed":12,"movement":"Tween","digmethod":"Remote","walkspeed":90,"jumpshortcuts":false,"walkspeed2":1.5,"walkdynamic":false},
"sprouts":{"enabled":true,"plant":true,"plantday":false,"collect":true,"amount":7,"left":5,"plantnight":true,"rarity3":false,"fieldsblacklist":false},
"stickbug":{"circle":true,"amulet":false,"totem":true,"boosts":[],"tickets":false,"keep":false,"loot":false,"values":[],"enabled":false,"spawn":false},
"webhook":{"console":false,"disconnectid":"","interval":5,"url":"","graphurl":"","stickers":false,"enabled":false,"graph":false,"beequips":false,"drives":false,"hidebranding":false,"questdone2":false,"items":false,"disconnect":false,"planters":true,"nectars":true,"balloon":false,"dappershop":false},
"memorymatch":{"ghost4":false,"night":false,"ghost2":false,"basic":false,"ghost":false,"mega":false,"extreme":false,"blacklist":false},
"rbc":{"passcooldown":0,"values":[],"upgrades":false,"mask":false,"rerollquests":false,"redtool":"Dark Scythe","bluemask":"Diamond Mask","cogconvert":true,"cogupgrades":true,"rerollupgrades":false,"materialsenabled":false,"buypass":false,"whitemask":"Gummy Mask","preset":"Blue","disableroundend":false,"maskround":5,"stoproundend":false,"whitetool":"Gummyballer","highestcogmax":10,"maxround":15,"highestcog":false,"precise":false,"rerollbees":false,"boosts":[],"bestredfield":"Mushroom Field","bestbluefield":"Blue Flower Field","keep":true,"tool":false,"amulet":true,"bluetool":"Tide Popper","toolround":4,"redmask":"Demon Mask","goomethod":"Gumdrops","bestwhitefield":"Sunflower Field","usedrives":{"Glitched":true,"Red":true,"Blue":true,"White":true},"buydrives":{"Glitched":true,"Red":true,"Blue":true,"White":true},"materials":false,"rerollmin":10,"upgradesenabled":false,"goldcogmowers":true,"enabled":false,"precisemin":5},
"beesmas":{"candles":false,"snowmachine":false,"snowflakeAt":95,"beesmasfeast":false,"snowflake":false,"honeymaskforwreath":false,"gingerbreadhouse":false,"partyspawn":false,"samovar":false,"roboparty":false,"partymobsbl2":false,"stockings":false,"coolbreeze":false,"wintermm":false,"onettlidart":false,"snowbear":false},
"toys":{"windshrine":false,"conversions":2,"stickerprinter":true,"stackselect":false,"sproutsummoner":false,"meteor":false,"honeystorm":false,"discardselect":false,"stickerstacker":false,"intwhitelist":false,"enabled":true,"wealthclock":false,"route":false,"hiddenstickers":true,"interrupt":true,"discardstickers":false,"shrineamount":1,"printereggs":{"Star Egg":true},"stackmethod":"Tickets","windsblacklist":false,"farmwinds":false,"nectarcondenser":false,"prog":true,"nectars":false,"progblender":true,"shrineitem":""},
"detected":{"rares":false,"fastcoconuttween":false,"fastshowertween":false,"fastraretween":false},
"snail":{"enabled":false,"keep":false,"amulet":false,"boosts":[],"values":[]},
"materials":{"enabled":[],"starsaw":false,"scorchingstar":[],"enabled2":false,"interval":[],"gummystar":[],"intervaltime":{"BlueExtract":15},"popstar":[]},
"puffshrooms":{"enabled":true,"rarity":"Common","max":3,"maintain":false,"highlvlpriority":false,"mintime":30,"min":1,"blacklistedfields":false,"priorityfields":false},
"planters":{"manual":{"farmfield":false,"planter3":{"harvestatpercentage":true,"plant":false,"ignoresmoking":false,"lastfield":false,"field2":"None","field1":"Dandelion Field","field4":"None","harvestat":100,"planter":"Plastic Planter","timetoharvest":4,"field3":"None","harvestaftertime":false,"harvest":false},"planter2":{"harvestatpercentage":true,"plant":false,"ignoresmoking":false,"lastfield":false,"field2":"None","field1":"Dandelion Field","field4":"None","harvestat":100,"planter":"Plastic Planter","timetoharvest":4,"field3":"None","harvestaftertime":false,"harvest":false},"planter1":{"harvestatpercentage":true,"plant":false,"ignoresmoking":false,"lastfield":false,"field2":"None","field1":"Dandelion Field","field4":"None","harvestat":100,"planter":"Plastic Planter","timetoharvest":4,"field3":"None","harvestaftertime":false,"harvest":false}},"method":"Manual","cycles":{"cycle1":{"planter1":{"field":"Dandelion Field","planter":"None"},"planter2":{"field":"Dandelion Field","planter":"None"},"planter3":{"field":"Dandelion Field","planter":"None"},"timetoharvest":2,"harvestat":100,"ignoresmoking":false,"harvestatpercentage":true,"harvestaftertime":false}},"enabled":false},
"antilag":{"textures":true,"precise":true,"flowers":true,"main":true,"bssui":false,"players":false,"norender":false,"tokens":true,"decorations":true,"bees":true,"stations":true,"particles":true,"balloons":true}
}
]]

    if not isfolder(folder) then
        makefolder(folder)
    end

    writefile(path, json)
end
LoadConfig()
task.spawn(function()
    while task.wait(3) do
        autoClaimStickers()
        autoDeleteStickers()
        autoPrinter()
    end
end)
while true do
    autoBuyEggTicket()
    checkStarSign()
    autoFeed()
    autoHatch()
    checkQuest()
    task.wait(5)
end
