
## Font color
COLOR = {
    'BLACK': '\x1b[30m', 
    'BLUE': '\x1b[34m', 
    'CYAN': '\x1b[36m', 
    'GREEN': '\x1b[32m', 
    'LIGHTBLACK_EX': '\x1b[90m', 
    'LIGHTBLUE_EX': '\x1b[94m', 
    'LIGHTCYAN_EX': '\x1b[96m', 
    'LIGHTGREEN_EX': '\x1b[92m', 
    'LIGHTMAGENTA_EX': '\x1b[95m', 
    'LIGHTRED_EX': '\x1b[91m', 
    'LIGHTWHITE_EX': '\x1b[97m', 
    'LIGHTYELLOW_EX': '\x1b[93m', 
    'MAGENTA': '\x1b[35m', 
    'RED': '\x1b[31m', 
    'RESET': '\x1b[39m', 
    'WHITE': '\x1b[37m', 
    'YELLOW': '\x1b[33m',
}
def set_color(text: str, key: str=None, value: str=None) -> str:
    if value == None:
        value = COLOR[key]
    return f"{value}{text}{COLOR['RESET']}"


## Font style
STYLE = {
    'BOLD': '\x1b[1m',
    'FAINT': '\x1b[2m',
    'ITALIC': '\x1b[3m',
    'UNDERLINE': '\x1b[4m',
    'INVERSE': '\x1b[7m',
    'STRIKETHROUGH': 'x1b[9m',
    'NORMAL': '\x1b[0m',    # END
}
def set_style(text: str, key: str=None, value: str=None) -> str:
    if value == None:
        value = STYLE[key]
    return f"{value}{text}{STYLE['NORMAL']}"