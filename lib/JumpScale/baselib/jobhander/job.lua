local jobraw=ARGV[2]

if redis.call("HEXISTS", "job.objects",ARGV[1])==1 then
    local job=cjson.decode()
    local jobrawdb=redis.call("HGET", "job.objects",ARGV[1])
    local jobdb=cjson.decode(jobrawdb)
    job["lasttime"]=job["epoch"]
    job["epoch"]=jobdb["epoch"]

redis.call("HSET", "job.objects",ARGV[1],jobraw)

if redis.call("HEXISTS", "job.last",ARGV[1])==0 then
    -- does not exist yet make sure queue knows about it
    redis.call("HSET", "job.last",ARGV[1],job["lasttime"])
    redis.call("RPUSH", "job.queue",ARGV[1])
else
    -- is already in queue lets checked when last time escalated, if more than 5 min put on queue
    local last=tonumber(redis.call("HGET", "job.last",ARGV[1]))
    if last<(job["lasttime"]-300) then
        --more than 5 min ago
        redis.call("RPUSH", "job.queue",ARGV[1])
        redis.call("HSET", "job.last",ARGV[1],job["lasttime"])
    end
end

if redis.call("LLEN", "job.queue") > 1000 then
    local todelete = redis.call("LPOP", "job.queue")
    redis.call("HDEL","job.objects",todelete)
    redis.call("HDEL","job.last",todelete)
end

return jobraw

