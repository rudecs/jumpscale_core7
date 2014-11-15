local eco=cjson.decode(ARGV[2])

if redis.call("HEXISTS", "eco:objects",ARGV[1])==1 then
    local ecoraw=redis.call("HGET", "eco:objects",ARGV[1])
    local ecodb=cjson.decode(ecoraw)
    ecodb["occurrences"]=ecodb["occurrences"]+1
    eco["occurrences"]=ecodb["occurrences"]
    eco["lasttime"]=eco["epoch"]
    eco["epoch"]=ecodb["epoch"]
    eco["guid"]=ecodb["guid"]
else
    eco["occurrences"]=1
    eco["lasttime"]=eco["epoch"]

end

local ecoraw=cjson.encode(eco)

redis.call("HSET", "eco:objects",ARGV[1],ecoraw)

if redis.call("HEXISTS", "eco:last",ARGV[1])==0 then
    -- does not exist yet make sure queue knows about it
    redis.call("HSET", "eco:last",ARGV[1],eco["lasttime"])
    redis.call("RPUSH", "queues:eco",ARGV[1])
else
    -- is already in queue lets checked when last time escalated, if more than 5 min put on queue
    local last=tonumber(redis.call("HGET", "eco:last",ARGV[1]))
    if last<(eco["lasttime"]-300) then
        --more than 5 min ago
        redis.call("RPUSH", "queues:eco",ARGV[1])
        redis.call("HSET", "eco:last",ARGV[1],eco["lasttime"])
    end
end

if redis.call("LLEN", "queues:eco") > 1000 then
    local todelete = redis.call("LPOP", "queues:eco")
    redis.call("HDEL","eco:objects",todelete)
    redis.call("HDEL","eco:last",todelete)
end

return ecoraw

