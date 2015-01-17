local turbo = require 'turbo'

local userslogoutHandler = class("userslogoutHandler", turbo.web.RequestHandler)
function userslogoutHandler:get()
    
    
    
    self:write("userslogoutHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
    }
    self:set_status(default)
--]]

end

local usersloginHandler = class("usersloginHandler", turbo.web.RequestHandler)
function usersloginHandler:get()
    -- query arguments
    local q_username = self:get_argument("username"  ,"" ) -- optional
    local q_password = self:get_argument("password"  ,"" ) -- optional

    
    
    self:write("usersloginHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
    }
    self:set_status(200)
    local response = {
    }
    self:set_status(400)
--]]

end

local userscreateWithListHandler = class("userscreateWithListHandler", turbo.web.RequestHandler)
function userscreateWithListHandler:post()
    
    
    --[[ body structure
    ]]--
    local body = self.request.body

    self:write("userscreateWithListHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
    }
    self:set_status(default)
--]]

end

local userscreateWithArrayHandler = class("userscreateWithArrayHandler", turbo.web.RequestHandler)
function userscreateWithArrayHandler:post()
    
    
    --[[ body structure
    ]]--
    local body = self.request.body

    self:write("userscreateWithArrayHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
    }
    self:set_status(default)
--]]

end

local usersusernameHandler = class("usersusernameHandler", turbo.web.RequestHandler)
function usersusernameHandler:put(username)
    
    
    --[[ body structure
    username - string
    firstName - string
    lastName - string
    userStatus - integer
    email - string
    phone - string
    password - string
    id - integer
    ]]--
    local body = self.request.body

    self:write("usersusernameHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
    }
    self:set_status(404)
    local response = {
    }
    self:set_status(400)
--]]

end
function usersusernameHandler:delete(username)
    
    
    
    self:write("usersusernameHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
    }
    self:set_status(404)
    local response = {
    }
    self:set_status(400)
--]]

end
function usersusernameHandler:get(username)
    
    
    
    self:write("usersusernameHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
        username = nil , -- type: string description: 
        firstName = nil , -- type: string description: 
        lastName = nil , -- type: string description: 
        userStatus = nil , -- type: integer description:User Status 
        email = nil , -- type: string description: 
        phone = nil , -- type: string description: 
        password = nil , -- type: string description: 
        id = nil 
    }
    self:set_status(200)
    local response = {
    }
    self:set_status(404)
    local response = {
    }
    self:set_status(400)
--]]

end

local usersHandler = class("usersHandler", turbo.web.RequestHandler)
function usersHandler:post()
    
    
    --[[ body structure
    username - string
    firstName - string
    lastName - string
    userStatus - integer
    email - string
    phone - string
    password - string
    id - integer
    ]]--
    local body = self.request.body

    self:write("usersHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
    }
    self:set_status(default)
--]]

end

local storesorderorderIdHandler = class("storesorderorderIdHandler", turbo.web.RequestHandler)
function storesorderorderIdHandler:delete(orderId)
    
    
    
    self:write("storesorderorderIdHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
    }
    self:set_status(404)
    local response = {
    }
    self:set_status(400)
--]]

end
function storesorderorderIdHandler:get(orderId)
    
    
    
    self:write("storesorderorderIdHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
        status = nil , -- type: string description:Order Status 
        shipDate = nil , -- type: string description: 
        complete = nil , -- type: boolean description: 
        petId = nil , -- type: integer description: 
        id = nil , -- type: integer description: 
        quantity = nil 
    }
    self:set_status(200)
    local response = {
    }
    self:set_status(404)
    local response = {
    }
    self:set_status(400)
--]]

end

local storesorderHandler = class("storesorderHandler", turbo.web.RequestHandler)
function storesorderHandler:post()
    
    
    --[[ body structure
    status - string
    shipDate - string
    complete - boolean
    petId - integer
    id - integer
    quantity - integer
    ]]--
    local body = self.request.body

    self:write("storesorderHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
        status = nil , -- type: string description:Order Status 
        shipDate = nil , -- type: string description: 
        complete = nil , -- type: boolean description: 
        petId = nil , -- type: integer description: 
        id = nil , -- type: integer description: 
        quantity = nil 
    }
    self:set_status(200)
    local response = {
    }
    self:set_status(400)
--]]

end

local petsfindByTagsHandler = class("petsfindByTagsHandler", turbo.web.RequestHandler)
function petsfindByTagsHandler:get()
    -- query arguments
    local q_tags = self:get_argument("tags"  ,"" ) -- optional

    
    
    self:write("petsfindByTagsHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
    }
    self:set_status(200)
    local response = {
    }
    self:set_status(400)
--]]

end

local petsfindByStatusHandler = class("petsfindByStatusHandler", turbo.web.RequestHandler)
function petsfindByStatusHandler:get()
    -- query arguments
    local q_status = self:get_argument("status"  ,"" ) -- optional

    
    
    self:write("petsfindByStatusHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
    }
    self:set_status(200)
    local response = {
    }
    self:set_status(400)
--]]

end

local petspetIdHandler = class("petspetIdHandler", turbo.web.RequestHandler)
function petspetIdHandler:post(petId)
    
    
    
    self:write("petspetIdHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
    }
    self:set_status(405)
--]]

end
function petspetIdHandler:delete(petId)
    
    -- header arguments
    local h_api_key = self.headers:get("api_key",false)

    
    self:write("petspetIdHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
    }
    self:set_status(400)
--]]

end
function petspetIdHandler:get(petId)
    
    
    
    self:write("petspetIdHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
        category = nil , -- type:  description: 
        status = nil , -- type: string description:pet status in the store 
        name = nil , -- type: string description: 
        tags = nil , -- type: array description: 
        photoUrls = nil , -- type: array description: 
        id = nil 
    }
    self:set_status(200)
    local response = {
    }
    self:set_status(404)
    local response = {
    }
    self:set_status(400)
--]]

end

local petsHandler = class("petsHandler", turbo.web.RequestHandler)
function petsHandler:put()
    
    
    --[[ body structure
    category - 
    status - string
    name - string
    tags - array
    photoUrls - array
    id - integer
    ]]--
    local body = self.request.body

    self:write("petsHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
    }
    self:set_status(405)
    local response = {
    }
    self:set_status(404)
    local response = {
    }
    self:set_status(400)
--]]

end
function petsHandler:post()
    
    
    --[[ body structure
    category - 
    status - string
    name - string
    tags - array
    photoUrls - array
    id - integer
    ]]--
    local body = self.request.body

    self:write("petsHandler\n")
    self:write("not implmented")
    self:set_status(500)

    --[[
--responses
    local response = {
    }
    self:set_status(405)
--]]

end

local app = turbo.web.Application:new({
        {"/api/users/logout", userslogoutHandler},
        {"/api/users/login", usersloginHandler},
        {"/api/users/createWithList", userscreateWithListHandler},
        {"/api/users/createWithArray", userscreateWithArrayHandler},
        {"/api/users/(.*)", usersusernameHandler},
        {"/api/users", usersHandler},
        {"/api/stores/order/(.*)", storesorderorderIdHandler},
        {"/api/stores/order", storesorderHandler},
        {"/api/pets/findByTags", petsfindByTagsHandler},
        {"/api/pets/findByStatus", petsfindByStatusHandler},
        {"/api/pets/(.*)", petspetIdHandler},
        {"/api/pets", petsHandler}
})
app:listen(8080,"0.0.0.0")
turbo.ioloop.instance():start()