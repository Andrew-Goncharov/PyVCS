import os
if not os.path.isdir("git"):
    os.mkdir("git")
    os.makedirs("git/refs/heads")
    os.makedirs("git/refs/tags")
    os.makedirs("git/objects")
    HEAD = open("git/HEAD", "w")
    HEAD.write("ref: refs/heads/master\n")
    config = open("git/config", "w")
    config.write("[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = false\n\tlogallrefupdates = false\n")
    description = open("git/description", "w")
    description.write("Unnamed pyvcs repository")
