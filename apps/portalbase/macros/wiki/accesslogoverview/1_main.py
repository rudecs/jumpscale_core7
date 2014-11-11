def main(j, args, params, tags, tasklet):
    print 'hello world'
    import time
    params.merge(args)
    doc = params.doc
    tags = params.tags.getDict()
    spacename = params.paramsExtra['space']
    out = ""
    logdir = j.core.portal.active.logdir
    backupdir = j.system.fs.joinPaths(logdir, 'backup')
    if 'filename' in tags.keys():
        filen = tags['filename']
        if not j.system.fs.exists(backupdir):
            j.system.fs.createDir(backupdir)
        originalfile = j.system.fs.joinPaths(logdir, filen)
        destfile = j.system.fs.joinPaths(backupdir, "%s_%s" % (time.ctime(), filen))
        j.system.fs.copyFile(originalfile, destfile)
        j.system.fs.writeFile(originalfile, "")

    spaces = j.core.portal.active.getSpaces()
    if spacename in spaces:
        sp = j.core.portal.active.getSpace(spacename)
    else:
        params.result = (out, params.doc)
        return params
    if spacename == 'system':
        logfiles = j.system.fs.listFilesInDir(logdir)
    else:
        logfiles = j.system.fs.joinPaths(logdir, 'space_%s.log') % spacename
    for lfile in logfiles:
        baselfile = j.system.fs.getBaseName(lfile)
        out += "|%s | [Reset | /system/ResetAccessLog?filename=%s] | [Show | system/ShowSpaceAccessLog?filename=%s]|\n" % (baselfile, baselfile, baselfile)

    params.result = (out, params.doc)
    return params


def match(j, args, params,  tags, tasklet):
    return True
