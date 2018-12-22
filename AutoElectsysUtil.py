import json
import platform

current_os = platform.system()
is_windows = current_os == 'Windows'
is_mac = current_os == 'Darwin'
is_64bit = '64' in platform.machine()

config_file_name = 'config.json'
pswd_file_name = 'jaccount.pswd'


def file_read_content(filename):
    with open(filename, 'rb') as fin:
        return fin.read()


def file_read_lines(filename, encoding='utf-8', strip_newline=True):
    with open(filename, 'r', encoding=encoding) as fin:
        for line in fin:
            if strip_newline:
                yield line.rstrip('\n')
            else:
                yield line


def file_read_json(filename, encoding='utf-8', **kw):
    with open(filename, 'r', encoding=encoding) as fin:
        return json.load(fin, **kw)


def file_write_content(filename, content):
    with open(filename, 'wb') as fout:
        fout.write(content)


def file_write_lines(filename, content, encoding='utf-8', append_newline=True):
    with open(filename, 'w', encoding=encoding) as fout:
        for line in content:
            fout.write(line)

            if append_newline:
                fout.write('\n')


def file_write_json(filename, content, encoding='utf-8', **kw):
    with open(filename, 'w', encoding=encoding) as fout:
        json.dump(content, fout, **kw)


def remove_utf8_bom(filename):
    if not is_windows:  # Only try to remove UTF-8 BOM on Windows.
        return

    try:
        content = file_read_content(filename)
    except Exception:  # If we cannot read this file, just silently give up.
        return

    if content[:3] != b'\xef\xbb\xbf':  # Detect whether UTF-8 BOM is present.
        return

    file_write_content(filename, content[3:])


def is_positive_int(s):
    try:
        return int(s) > 0
    except Exception:
        return False
