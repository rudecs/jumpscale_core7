import os

acl_cfg = '''all:R
admin:*
guests:R
guest:R
'''

main_cfg = '''[main]
id = cloudscalers_operations
'''

default_wiki = '''
    {{title:New Portal}}
    {{projectname:New Portal}}
    {{menu:
    }}
    {{menuloggedin:
    Home:Home
    }}
    {{menuadmin}}

    @block
    @row

    @col 3
    {{navigation}}
    @divend

    @col 9

    {content}

    @divend
    @divend


    {{cssstyle
    td {
        max-width:500px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;}
    }}
'''

def main(j, args, params, tags, tasklet):
    params.result = page = args.page

    portal = j.core.portal.active
    contentdir = args.paramsExtra.get('contentdir')
    space_path = args.paramsExtra.get('space_path')

    if contentdir and space_path:
        if os.path.exists(space_path):
            page.addMessage('***ERROR***: The space path "{}" already exists'.format(space_path))
            return params

        if not os.path.exists(contentdir):
            page.addMessage('***ERROR***: The content dir "{}" does not exist'.format(contentdir))
            return params

        os.makedirs(os.path.join(space_path, '.space'))
        os.symlink(space_path, os.path.join(contentdir, os.path.basename(space_path)))

        with open(os.path.join(space_path, '.space', 'acl.cfg'), 'w') as f:
            f.write(acl_cfg)

        with open(os.path.join(space_path, '.space', 'main.cfg'), 'w') as f:
            f.write(main_cfg)

        with open(os.path.join(space_path, '.space', 'nav.wiki'), 'w') as f:
            f.write('Home:Home')

        with open(os.path.join(space_path, '.space', 'default.wiki'), 'w') as f:
            f.write(default_wiki)

        with open(os.path.join(space_path, 'Home.wiki'), 'w') as f:
            f.write('@usedefault\nWelcome to the new space\nThis space lives in `{}`'.format(space_path))

        
        portal.spacesloader = j.core.portalloader.getSpacesLoader()
        portal.spacesloader.scan(portal.contentdirs)

        page.addMessage('Created successfully. Click <a href="/{}/">here</a> to go to the new portal'.format(os.path.basename(space_path)))

    else:
        contentdirs = ''.join('<option value="{0}">{0}</option>'.format(d) for d in portal.contentdirs)

        page.addMessage('''
            <form class="form-horizontal" method="get" action="/system/createspace">
                <fieldset>
                    <div class="control-group">
                        <label class="control-label" for="space_path">Path to space</label>
                        <div class="controls">
                            <input name="space_path" type="text" placeholder="" class="input-xxlarge" required="" value="/opt/code/incubaid/www_<my_space>">
                        </div>
                    </div>

                    <div class="control-group">
                        <label class="control-label" for="contentdir">Content Directory</label>
                        <div class="controls" name="contentdir">
                            <select name="contentdir" id="contentdir" class="input-xxlarge">
                            {0}
                            </select>
                        </div>
                    </div>

                    <div class="control-group">
                        <div class="controls">
                            <button class="btn btn-primary">Create</button>
                        </div>
                    </div>

                </fieldset>
            </form>'''.format(contentdirs))

    return params


def match(j, args, params, tags, tasklet):
    return True
