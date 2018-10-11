
def edit_command(conf, notebook_step):
    if len(conf):
        return "editing notebook " + " : " + notebook_step
    else:
        return "no configurations for " + notebook_step
