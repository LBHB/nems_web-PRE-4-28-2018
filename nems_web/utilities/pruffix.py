""" Utility functions for parsing a list of modelnames into a list of
abbreviated strings with a common prefix and/or suffix.
@author jacob
"""
import logging
log = logging.getLogger(__name__)


def find_prefix(s_list):
    """Given a list of strings, returns the common prefix to nearest _."""
    prefix = ''
    if (not s_list) or (len(s_list) == 1):
        return prefix
    i = 0
    test = True
    while test:
        # log.debug('while loop, i=%s'%i)
        # log.debug('before for loop, prefix = %s'%prefix)
        for j in range(len(s_list) - 1):
            # look at ith item of each string in list, in order
            if i < len(s_list[j]):
                a = s_list[j][i]
            else:
                a = ''
            if i<len(s_list[j+1]):
                b = s_list[j + 1][i]
            else:
                b = ''
            # log.debug('for loop, a = %s and b = %s'%(a, b))
            if a != b:
                test = False
                break
            if j == len(s_list) - 2:
                prefix += b
        i += 1

    while prefix and (prefix[-1] != '_'):
        prefix = prefix[:-1]

    return prefix


def find_suffix(s_list):
    """Given a list of strings, returns the common suffix to nearest _."""
    suffix = ''
    if (not s_list) or (len(s_list) == 1):
        return suffix
    i = 1
    test = True
    while test:
        # log.debug('while loop, i=%s'%i)
        # log.debug('before for loop, suffix = %s'%suffix)
        for j in range(len(s_list) - 1):
            # look at ith item of each string in reverse order
            a = s_list[j][-1 * i]
            b = s_list[j + 1][-1 * i]
            # print('for loop, a = %s and b = %s'%(a, b))
            if a != b:
                test = False
                break
            if j == len(s_list) - 2:
                suffix += b
        i += 1
    # reverse the order so that it comes out as read left to right
    suffix = suffix[::-1]
    while suffix and (suffix[0] != '_'):
        suffix = suffix[1:]

    return suffix


def find_common(s_list, pre=True, suf=True):
    """Given a list of strings, finds the common suffix and prefix, then
    returns a 3-tuple containing:
        index 0, a new list with prefixes and suffixes removed
        index 1, the prefix that was found.
        index 2, the suffix that was found.
    Takes s_list as list of strings (required), and pre and suf as Booleans
    (optional) to indicate whether prefix and suffix should be found. Both are
    set to True by default.
    """

    prefix = ''
    if pre:
        log.debug("Finding prefixes...")
        prefix = find_prefix(s_list)
    suffix = ''
    if suf:
        log.debug("Finding suffixes...")
        suffix = find_suffix(s_list)
    # shortened = [s[len(prefix):-1*(len(suffix))] for s in s_list]
    shortened = []
    for s in s_list:
        # log.debug("s=%s"%s)
        if prefix:
            s = s[len(prefix):]
            # log.debug("s changed to: %s"%s)
        if suffix:
            s = s[:-1 * len(suffix)]
            # log.debug("s changed to: %s"%s)
        shortened.append(s)
        log.debug("final s: %s" % s)

    return (shortened, prefix, suffix)
