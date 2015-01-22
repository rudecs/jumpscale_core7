
--
-- An echo jumpscript that returns the passed message argument it received.
--
-- Keyword args:
--  message (str): the message to be echoed back
--

M = {}

function M.main(args)
  return args.message
end

return M