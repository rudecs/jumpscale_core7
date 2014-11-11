
def main(j, args, params, tags, tasklet):

    doc = params.doc

    e = params.requestContext.env

    addr = j.core.portal.runningPortal.ipaddr

    querystr = e["QUERY_STRING"]
    querystr = querystr.replace("&format=text", "")
    querystr = querystr.replace("&key=,", "")
    querystr = querystr.replace("&key=", "")
    querystr = querystr.replace("key=,", "")
    querystr = querystr.replace("key=", "")
    querystr += "key=%s" % j.apps.system.usermanager.extensions.usermanager.getUserFromCTX(params.requestContext).secret

    if "machine" in params:
        url = "http://" + addr +\
            e["PATH_INFO"].strip("/") + "?" + querystr
        params.page.addLink(url, url)
    else:
        url = "http://" + addr + "/restmachine/" +\
            e["PATH_INFO"].replace("/rest/", "").strip("/") + "?" + querystr

        params.page.addLink(url, url)
        params.page.addMessage("Be carefull generated key above has been generated for you as administrator.")

    return params


def match(j, args, params, tags, tasklet):
    return True
