
lua_add = {}

--
-- Adds the two int arguments x, and y and returns the result.
--
function lua_add.main(args)
  return tonumber(args.x) + tonumber(args.y)
end

return lua_add
