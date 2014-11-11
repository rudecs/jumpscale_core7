def main(j, args, params, tags, tasklet):
    params.merge(args)

    doc = params.doc
    out="{{datatables_use}}}}\n\n"

    out+="||GID||Name||Email||Active||Groups||\n"
    users = j.core.portal.active.auth.listUsers()
    for user in users:
        user['groups'] = ', '.join(user['groups'])
        out += "|%(gid)s|%(id)s|%(emails)s|%(active)s|%(groups)s|\n" % user


    params.result = (out, doc)

    return params


def match(j, args, params, tags, tasklet):
    return True
