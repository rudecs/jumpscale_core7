if redis.call("LLEN", "queues:logs") > 2000 then
    redis.call("LPOP", "qeues:logs")
end

redis.call("RPUSH", "queues:logs",ARGV[1])
return "OK"

