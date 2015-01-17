local github = require 'Spore'.new_from_spec 'github.json'
github:enable 'Format.JSON'
github:enable('Auth.Basic', {
    username = 'schacon/token',
    password = '6ef8395fecf207165f1a82178ae1b984',
})
local res = github:get_info{format = 'json', username = 'schacon'}
print(res.status)               --> 200
print(res.headers['x-runtime']) --> 126ms
print(res.body.user.name)       --> Scott Chacon