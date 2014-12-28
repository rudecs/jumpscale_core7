from JumpScale import j

descr = """gets jpackage file info"""

name = "jpackage_fileinfo"
category = "jpackages"
organization = "jumpscale"
author = "deboeckj@codescalers.com"
version = "1.0"

gid, nid, _ = j.application.whoAmI
roles = []


def action(domain, pname, version):
    if version and domain and pname:
        package = j.packages.find(domain, pname, version)[0]
    else:
        if domain and pname:
            package = j.packages.findNewest(domain, pname)
            if not package:
                return False
        else:
            return False
    aaData = list()
    if package:
        for platform,ttype in package.getBlobPlatformTypes():
            blobinfo = package.getBlobInfo(platform, ttype)
            for entry in blobinfo[1]:
                aaData.append([platform,ttype,entry[1],entry[0]])
    return aaData
