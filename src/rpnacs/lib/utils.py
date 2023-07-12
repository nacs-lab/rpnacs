def rm_err(text):
    if text.startswith('ERR!'):
        return 1, text[4:len(text)]
    return 0, text
