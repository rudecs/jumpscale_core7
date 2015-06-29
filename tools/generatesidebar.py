import os

path = os.getcwd()

for root, folders, files in os.walk(path):
    basename = os.path.basename(root)
    index = "# %s\n\n" % basename
    for folder in folders:
        index += "* [{0}]({0})\n".format(folder)
    for file in files:
        if file == '_Sidebar.md' or file == "%s.md" % basename:
            continue
        index += "* [{0}]({0})\n".format(os.path.splitext(file)[0])

    parent = os.path.basename(os.path.dirname(root))
    index += "* [[{0}]({0})]\n".format(parent)
    sidebar = os.path.join(root, '_Sidebar.md')
    file = open(sidebar, 'w+')
    file.write(index)
    file.close()
    folderhome = os.path.join(root, '%s.md' % basename)
    if not os.path.exists(folderhome):
        file = open(folderhome, 'w+')
        file.write(index)
        file.close()
