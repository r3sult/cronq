def split_command(string):
    commands = string.strip().split(';')
    ret = []
    for command in commands:
        ret.extend(command.strip().split(' && '))
    return ret
