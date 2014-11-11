
def main(j, args, params, tags, tasklet):
    params.merge(args)

    doc = params.doc

    params.result = ""


    spaces = sorted(j.core.portal.active.getSpaces())
    spacestxt=""
    for item in sorted(spaces):
        if item[0] != "_" and item.strip() != "" and item.find("space_system")==-1 and item not in ["help","system"]:
            name = j.core.portal.active.getSpace(item, ignore_doc_processor=True).model.id
            spacestxt += "%s:/%s\n" % (name, item.lower().strip("/"))


    C = """
{{menudropdown: name:Portal
New Page:/system/create
Edit Page:/system/edit?space=$$space&page=$$page$$querystr
Create Space:/system/createspace
--------------
Files:/system/files?space=$$space
--------------
Logout:/system/login?user_logoff_=1
Access:/system/OverviewAccess?space=$$space
Reload:javascript:$.ajax({'url': '/system/ReloadSpace?name=$$space'}).done(function(){location.reload()});void(0);
ReloadAll:javascript:reloadAll();void 0;
Pull latest changes & update:javascript:pullUpdate('$$space');void 0;
--------------
"""
    C+=spacestxt
    C+='}}'

    C+='''
    {{htmlhead:
    <script type="text/javascript" src="/jslib/old/adminmenu/adminmenu.js"></script>
    }}
    '''

#was inside
#ShowLogs:/system/ShowSpaceAccessLog?space=$$space
#ResetLogs:/system/ResetAccessLog?space=$$space
#Spaces:/system/Spaces
#Pages:/system/Pages?space=$$space

    if j.core.portal.active.isAdminFromCTX(params.requestContext):
        params.result = C

    params.result = (params.result, doc)

    return params


def match(j, args, params, tags, tasklet):
    return True
