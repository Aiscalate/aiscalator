def run_command(conf, notebook_step):
    if len(conf):
        return "running notebook " + " : " + notebook_step
    else:
        return "no configurations for " + notebook_step
