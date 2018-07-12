import subprocess

def run_command_background(command):
    return subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, start_new_session=True)


def run_command(commad):
    return subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)


def run_shell(command):
    return subprocess.run(command, shell=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)