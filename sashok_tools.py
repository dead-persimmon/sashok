import re

tags_1st_pass = ['h264', 'h-264', 'h.264'
                 'blu-ray']

tags_2nd_pass = ['480p', '720p', '1080p',
               'hi10p',
               'h264', 'h-264', 'h.264',
               'aac', 'flac',
               'dvd', 'blu-ray', 'bluray']



re_crc = re.compile('\[[0-9abcdef]{8}\]', re.I)

re_tags_1st_pass = re.compile('|'.join(re.escape(tag) for tag in tags_1st_pass), re.I)


re_extract_tags = re.compile('\[[.!\]]+\]')

def separate_tags(string, brackets = '[]'):
    tags = []
    while True:
        opening_index = string.find(brackets[0])
        if opening_index > -1:
            balance = 0
            for index, char in enumerate(string[opening_index:]):
                if char == brackets[0]: balance += 1
                elif char == brackets[1]: balance -= 1
                if balance == 0:
                    closing_index = opening_index + index
                    tags.append(string[opening_index+1:closing_index])
                    string = string[:opening_index] + string[closing_index+1:]
                    break
            if balance != 0:
                return string, None
        else: break
    return string, tags

re_extension = re.compile('|'.join(re.escape(ext) for ext in ('.avi', '.mkv', '.mp4')), re.I)
re_underscores = re.compile('_+')
re_numbers = re.compile('[0-9]+')
re_floating_dash = re.compile('\s\-\s')
re_dots = re.compile('\.+')
re_multibangs = re.compile('\!+')

re_spaces = re.compile('\s+')


def normalize_filename(string):
    original_string = string

    string, square_tags = separate_tags(string, brackets = '[]')
    string, round_tags = separate_tags(string, brackets = '()')
    tags = (square_tags or []) + (round_tags or [])
    
    string = re_extension.sub('', string)
    string = re_underscores.sub(' ', string)
    string = re_numbers.sub('', string)
    string = re_floating_dash.sub(' ', string)

    if string.find(' ') == -1:
        string = re_dots.sub(' ', string)
    string = re_multibangs.sub('!', string)

    string = re_spaces.sub(' ', string)
    string = string.strip()

    
    #for char, index in enumerate(norm_string):
    #    if char == '[':
    
    #tags = re_extract_tags.match(norm_string)
    #print(tags)
    #norm_string = re_crc.sub('~CRC~', norm_string)
    #norm_string = re_extension.sub('~EXT~', norm_string)
    #norm_string = re_tags_1st_pass.sub('~TAG~', norm_string)
    #norm_string = re_restore_spaces.sub(' ', norm_string)
    
    #norm_string = re_common_tags.sub('', norm_string)
    #norm_string = re_numbers.sub('__NUM__', norm_string)
    return string, tags, original_string
 
 
#normalize_filename()