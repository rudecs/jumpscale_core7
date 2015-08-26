
--key,measurement,value,str(now),type,tags

local key=KEYS[1]
local measurement=ARGV[1]
local value = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local type=ARGV[4]
local tags=ARGV[5]
local node=ARGV[6]

local hsetkey =string.format("stats:%s",node)
local v= {}
local c=""
local m 
local prev = redis.call('HGET',hsetkey,key)

if prev then
    v = cjson.decode(prev)
    local diff
    local difftime

    if type=="D" then
        -- diff
        diff = tonumber(value)-v["val"]
        difftime = now-v["epoch"]
        m=math.floor((diff*1000/difftime)+0.5)
    else
        m=tonumber(value)
    end

    -- if v["m_epoch"]< (now-(1000*60)) then
    --     v["m_total"]=0
    --     v["m_nr"]=0
    --     v["m_epoch"] = now
    -- end
    -- if v["h_epoch"]< (now-(1000*60*60)) then
    --     v["h_total"]=0
    --     v["h_nr"]=0
    --     v["h_epoch"] = now
    -- end


    v["m_last"]=m
    v["m_total"]=v["m_total"]+m
    v["m_nr"]=v["m_nr"]+1
    v["m_avg"]= v["m_total"]/v["m_nr"]
    v['val'] = value
    v["epoch"]= now
    v["h_epoch"]= now
    v["m_epoch"]= now
    if m>v["m_max"] then
        v["m_max"]=m
    end
    v["h_total"]=v["h_total"]+m
    v["h_nr"]=v["h_nr"]+1
    v["h_avg"]= v["h_total"]/v["h_nr"]
    if m>v["h_max"] then
        v["h_max"]=m
    end

    redis.call('HSET',hsetkey,KEYS[1],cjson.encode(v))

    local nowshort=math.floor(now/1000+0.5)

    c=string.format("%s|%s|%s|%u|%u|%u|%u|%u|%u",measurement,key,tags,nowshort,m,v["m_avg"],v["m_max"],v["h_avg"],v["h_max"])

    if redis.call("LLEN", "queues:stats") > 200000 then
        redis.call("LPOP", "qeues:stats")
    end
    redis.call("RPUSH", "queues:stats",c)
    return m
else
    v["m_avg"]= 0
    v["m_last"]= 0
    v["m_epoch"]= now
    v["m_total"]= value
    v["m_max"]= 0
    v["m_nr"]= 0
    v["h_avg"]= 0
    v["h_epoch"]= now
    v["h_total"]= 0
    v["h_nr"]= 0
    v["h_max"]= 0
    v["epoch"]= now
    v["val"]= value
    redis.call('HSET',hsetkey,KEYS[1],cjson.encode(v))
    -- prev = redis.call('HGET',"stats",KEYS[1])
    return 0
end





-- return cjson.encode(v)

