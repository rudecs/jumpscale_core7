import os, subprocess

def main(j, args, params, tags, tasklet):
    params.result = page = args.page

    space_name = args.cmdstr.strip()
    space = j.core.portal.active.getSpace(space_name)
    space_path = os.path.abspath(space.model.path)
    current_dir = os.getcwd()

    try:
        os.chdir(space_path)
        process = subprocess.Popen(['hg', 'pull'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        output, error = process.communicate()
        if error:
            page.addMessage(error)
            return params
        else:
            page.addMessage('Pulled')

        process = subprocess.Popen(['hg', 'update', '--clean'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        output, error = process.communicate()
        if error:
            page.addMessage(error)
            return params
        else:
            page.addMessage('Updated')
        
    finally:
        os.chdir(current_dir)

    return params


def match(j, args, params, tags, tasklet):
    return True
