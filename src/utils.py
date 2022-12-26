def split_str_by_len(str, maxlen) -> list:
    '''
    Splits a string in array of strings with a max size
    '''
    return [str[ind:ind + maxlen] for ind in range(0, len(str), maxlen)]
