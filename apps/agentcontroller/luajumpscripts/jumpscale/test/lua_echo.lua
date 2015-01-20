
--
-- An echo jumpscript that write the passed message argument to STDOUT.
--
-- Keyword args:
--  message (str): the message to be echoed back
--

M = {}

function M.main(args)
  print(args.message)
end

return M