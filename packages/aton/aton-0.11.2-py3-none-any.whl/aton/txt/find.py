"""
# Description

Functions to search for specific content inside text files.


# Index

Find and return specific text strings from a file  
`lines()`  
`between()`  

Find the `(start, end)` position of specific strings in a file  
`pos()`  
`pos_regex()`  
`next_pos()`  
`next_pos_regex()`  
`line_pos()`  
`between_pos()`  


# Examples

To find the lines containing the word 'key', plus an additional line below,
```python
from aton import txt
# with split = False
txt.find.lines(filepath=file, key='key', additional=1)
    # ['line with key 1\\nline below first match',
    #  'line with key 2\\nline below second match]
# with split = True
txt.find.lines(filepath=file, key='key', additional=1, split=True)
    # ['line with key 1',
    # 'line below first match',
    # 'line with key 2',
    # 'line below second match]
```

To find the text between the lines containing the words 'first' and 'second',
```python
from aton import txt
txt.find.between(filepath=file, key1='first', key2='second')
    # 'first line\\nadditional\\nlines\\nin\\nbetween\\nsecond line'
```

---
"""


import mmap
import re
import aton.file as file


def lines(
        filepath:str,
        key:str,
        matches:int=0,
        additional:int=0,
        split: bool=False,
        regex:bool=False
    ) -> list:
    """Returns a list with the matches containing the `key` string in `filepath`.

    If no match is found, returns an empty list.

    To use regular expressions in the search, set `regex=True`
    (deactivated by default).

    The value `matches` specifies the max number of matches to be returned.
    Defaults to 0 to return all possible matches. Set it to 1 to return only one match,
    or to negative integers to start the search from the end of the file upwards.

    The value `additional` specifies the number of additional lines
    below the target line that are also returned;
    2 to return the found line plus two additional lines below, etc.
    Negative values return the specified number of lines before the target line.
    The original ordering from the file is preserved.
    Defaults to `additional=0`, only returning the target line.
    By default, the additional lines are returned
    in the same list item as the match separated by a `\\n`,
    unless `split=True`, in which case these additional lines
    are splitted and added as additional items in the list.
    """
    file_path = file.get(filepath)
    matches_found = []
    if regex:
        positions = pos_regex(file_path, key, matches)
    else:
        positions = pos(file_path, key, matches)
    with open(file_path, 'r+b') as f:
        try:
            mm = mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ)
        except ValueError:
            return []
    for start, end in positions:
        # Get the positions of the full line containing the match
        line_start = mm.rfind(b'\n', 0, start) + 1
        line_end = mm.find(b'\n', end, len(mm))
        # Default values for the start and end of the line
        if line_start == -1: line_start = 0
        if line_end == -1: line_end = len(mm)
        # Adjust the line_end to add additional lines after the match
        match_start = line_start
        match_end = line_end
        if additional > 0:
            for _ in range(abs(additional)):
                match_end = mm.find(b'\n', match_end + 1, len(mm)-1)
                if match_end == -1:
                    match_end = len(mm)
                    break
        elif additional < 0:
            for _ in range(abs(additional)):
                match_start = mm.rfind(b'\n', 0, match_start - 1) + 1
                if match_start == -1:
                    match_start = 0
                    break
        # Save the matched lines
        matches_found.append(mm[match_start:match_end].decode())
    if split:
        splitted_matches_found = []
        for string in matches_found:
            splitted_match = string.splitlines()
            splitted_matches_found.extend(splitted_match)
        matches_found = splitted_matches_found
    return matches_found


def between(
        filepath:str,
        key1:str,
        key2:str,
        include_keys:bool=True,
        match:int=1,
        regex:bool=False
    ) -> str:
    """Returns the content between the lines with `key1` and `key2` in `filepath`.

    Keywords can be at any position within the line.
    Regular expressions can be used by setting `regex=True`.

    Key lines are omited by default, but can be returned with `include_keys=True`.

    If there is more than one match, only the first one is considered by default;
    set `match` (int) to specify a particular match (1, 2... 0 is considered as 1!).
    Use negative numbers to start from the end of the file.

    If no match is found, returns an empty string.

    If `key2` is not found, it returns all the text from `key1` to the end of the file.
    """
    file_path = file.get(filepath)
    start, end = between_pos(file_path, key1, key2, include_keys, match, regex)
    if (start, end) == (-1, -1):
        return ''
    with open(file_path, 'r+b') as f:
        try:
            mm = mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ)
        except ValueError:
            return ''
    return (mm[start:end].decode())


def pos(
        filepath,
        key:str,
        matches:int=0,
        ) -> list:
    """Returns a list with the positions of the `key` in `filepath`.

    If no match is found, returns an empty list.

    The `filepath` can be a file or a memory mapped file.

    The value `matches` specifies the max number of matches to return.
    Defaults to 0 to return all possible matches.
    Set it to 1 to return only one match,
    2 to get the first two matches, etc.
    You can also set it to negative integers to start
    searching from the end of the file upwards.



    This method is faster than `pos_regex()`,
    but does not search for regular expressions.
    """
    positions = []
    mm = filepath
    if not isinstance(filepath, mmap.mmap):
        file_path = file.get(filepath)
        with open(file_path, 'r+b') as f:
            try:
                mm = mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ)
            except ValueError:
                return [(-1, -1)]        ######################   TODO Should it return this if the file is empty?
    keyword_bytes = key.encode()
    if matches >= 0:
        start = 0
        while matches == 0 or len(positions) < matches:
            pos = mm.find(keyword_bytes, start)
            if pos == -1:
                break
            end = pos + len(keyword_bytes)
            positions.append((pos, end))
            start = end
    else:
        start = len(mm)
        while len(positions) < abs(matches):
            pos = mm.rfind(keyword_bytes, 0, start)
            if pos == -1:
                break
            end = pos + len(keyword_bytes)
            positions.append((pos, end))
            start = pos
        positions.reverse()
    return positions


def pos_regex(
        filepath,
        key:str,
        matches:int=0
    ) -> list:
    """Returns a list of the positions of a `key` in a given `filepath` (actual file, not mmapped!).

    The value `matches` specifies the max number of matches to return.
    Defaults to 0 to return all possible matches. Set it to 1 to return only one match,
    or to negative integers to start searching from the end of the file upwards.

    For big files, this method is slower than `pos()`, but it can search for regular expressions.
    """
    file_path = file.get(filepath)
    positions = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    if matches > 0:
        start = 0
        while len(positions) < matches:
            match = re.search(key, content[start:], flags=re.MULTILINE)  # MULTILINE for ^ regex
            if not match:
                break
            match_start = start + match.start()
            match_end = start + match.end()
            positions.append((match_start, match_end))
            start = match_end
    else:
        all_matches = list(re.finditer(key, content, flags=re.MULTILINE))
        if matches == 0:
            positions = [(match.start(), match.end()) for match in all_matches]
        else:
            positions = [(match.start(), match.end()) for match in all_matches[-abs(matches):]]
    return positions


def next_pos(
        filepath,
        position:tuple,
        key:str,
        match:int=1
    ) -> tuple:
    """Get the next position of the `key` in the `filepath` (file or mmapped file), starting from an initial `position` tuple.

    The `match` number specifies the nonzero index of the next match to return (1, 2... 0 is considered as 1!).
    It can be negative to search backwards from the initial position.
    The last known positions will be returned if no more matches are found.

    This method is specific for normal strings.
    To use regular expressions, check `next_pos_regex()`.
    """
    mm = filepath
    if not isinstance(filepath, mmap.mmap):
        file_path = file.get(filepath)
        with open(file_path, 'r+b') as f:
            try:
                mm = mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ)
            except ValueError:                ###########  TODO  what should this return?? 
                return (-1, -1)
    start, end = position
    keyword_bytes = key.encode()
    if match == 0:
        match = 1
    positions = []
    if match > 0:
        for _ in range(match):
            start = mm.find(keyword_bytes, end, len(mm))
            if start == -1:
                break
            end = start + len(keyword_bytes)
            positions.append((start, end))
    else:
        for _ in range(abs(match)):
            start = mm.rfind(keyword_bytes, 0, start)
            if start == -1:
                break
            end = start + len(keyword_bytes)
            positions.append((start, end))
    positions.reverse()
    if len(positions) == 0:               ###########  TODO  what should this return?? 
        positions.append((-1, -1))
    return positions[0]                     #####  should return empty if not found?


def next_pos_regex(
        filepath,
        position:tuple,
        key:str,
        match:int=0
    ) -> tuple:
    """Get the next position of the `key` in the `filepath` (actual file, not mmapped!), starting from an initial `position` tuple.

    The `match` number specifies the next match to return (1, 2... 0 is considered as 1!).
    It can be negative to search backwards from the initial position.
    This method is specific for regular expressions.

    For normal strings, check the faster `next_pos()` method.
    """
    file_path = file.get(filepath)
    start, end = position
    with open(file_path, 'r') as f:
        content = f.read()
    if match == 0:
        match = 1
    positions = []
    if match > 0:
        for _ in range(match):
            match_found = re.search(key, content[end:])
            if not match_found:
                break
            start = end + match_found.start()
            end = end + match_found.end()
            positions.append((start, end))
        positions.reverse()
        if len(positions) == 0:  ###########  when pos did not find, it was []  !! should be same here?
            positions.append((-1, -1))
        return positions[0]
    else:  # Reverse match
        all_matches = list(re.finditer(key, content))
        if not all_matches:  ###########   when pos did not find, it was []  !! should be same here?
            return (-1, -1)
        if abs(match) > len(all_matches):
            match = -len(all_matches)
        else:
            match_found = all_matches[match]  # Already negative
            start = match_found.start()
            end = match_found.end()
    return start, end


def line_pos(
        filepath,
        position:tuple,
        skips:int=0
    ) -> tuple:
    """Get the position of the full line containing the `position` tuple in `filepath` (whether file or memory mapped file).

    A specific line below can be returned with `skips` being a natural int,
    or previous lines with negative values.
    """
    mm = filepath
    if not isinstance(filepath, mmap.mmap):
        file_path = file.get(filepath)
        with open(file_path, 'r+b') as f:
            try:
                mm = mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ)
            except ValueError:
                return (-1, -1)
    if position == (-1, -1):  # No match
        return (-1, -1)
    start, end = position
    if skips == 0:
        start = mm.rfind(b'\n', 0, start) + 1
        end = mm.find(b'\n', end, len(mm))
    elif skips > 0:
        for i in range(0, abs(skips)):
            start = mm.find(b'\n', end, len(mm)) + 1
            if start == -1:
                start = len(mm)
                end = len(mm)
                break
            end = mm.find(b'\n', start, len(mm))
            if end == -1:
                start = len(mm)
                end = len(mm)
                break
    else:  # previous lines
        for i in range(0, abs(skips)):
            end = mm.rfind(b'\n', 0, start)
            if end == -1:
                start = 0
                end = 0
                break
            start = mm.rfind(b'\n', 0, end) + 1
            if start == -1:
                start = 0
                end = 0
                break
    return start, end


def between_pos(
        filepath,
        key1:str,
        key2:str,
        include_keys:bool=True,
        match:int=1,
        regex:bool=False
    ) -> tuple:
    """Returns the positions of the content between the lines containing `key1` and `key2` in the `filepath`.

    Keywords can be at any position within the line.
    Regular expressions can be used by setting `regex=True`.

    Key lines are omited by default, but can be returned with `include_keys=True`.

    If there is more than one match, only the first one is considered by default;
    set `match` number to specify a particular match (1, 2... 0 is considered as 1!).
    Use negative numbers to start from the end of the file.

    If `key2` is not found, it returns the text position from `key1` to the end of the file.
    """
    file_path = file.get(filepath)
    if match == 0:
        match = 1
    if regex:
        positions_1: list = pos_regex(file_path, key1, match)
        if not positions_1:
            return (-1, -1)
        if match > 0:
            positions_1.reverse()
        position_1 = positions_1[0]
        position_2: tuple = next_pos_regex(file_path, position_1, key2, 1)
    else:
        positions_1: list = pos(file_path, key1, match)
        if not positions_1:
            return (-1, -1)
        if match > 0:
            positions_1.reverse()
        position_1 = positions_1[0]
        position_2: tuple = next_pos(file_path, position_1, key2, 1)
    skip_line_1 = 0
    skip_line_2 = 0
    if not include_keys:
        skip_line_1 = 1
        skip_line_2 = -1
    with open(file_path, 'r+b') as f:
        try:
            mm = mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ)
        except ValueError:
            return (-1, -1)
    start, _ = line_pos(mm, position_1, skip_line_1)
    if position_2 != (-1, -1):
        _, end = line_pos(mm, position_2, skip_line_2)
    else:
        end = len(mm)
    return start, end

