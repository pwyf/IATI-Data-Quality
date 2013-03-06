import re
import itertools
from functools import partial

class TestSyntaxError(Exception): pass

comment = re.compile('#')
blank = re.compile('^$')

def ignore_line(line):
    return bool(comment.match(line) or blank.match(line))


def generate_test_functions(tests):
    mappings = []

    def add(regex):
        def append_to_mappings(fn):
            mappings.append((re.compile(regex),fn))
            return fn
        return append_to_mappings

    def add_partial(regex):
        def append_to_mappings(fn):
            def partial_fn(groups):
                return partial(fn, groups=groups)
            mappings.append((re.compile(regex), partial_fn))
            return fn
        return append_to_mappings

    @add('(\S*) is an? (.*)\?')
    def is_an(groups):
        if groups[1] == 'iso date':
            return None
        elif groups[1] == 'integer':
            def int_check(x):
                try:
                    int(x)
                    return True
                except ValueError:
                    return False
            def is_an_integer(activity):
                return reduce(lambda x,y: x and y,
                            map(lambda x: int_check(x),
                                    activity.xpath(groups[0])),
                            False)
            return is_an_integer

    @add_partial('(\S*) has more than (\S*) characters\?')
    def text_chars(activity, groups):
        return bool(reduce(lambda x,y: x or y,
                        map(lambda x: len(x)>int(groups[1]),
                            activity.xpath(groups[0])),
                        False))

    def rm_blank(alist):
        return filter(lambda x: x!='', alist)

    @add_partial('(\S*) sum to (\S*)\?')
    def sum(activity, groups):
        return (reduce(lambda x,y: float(x)+float(y),
                           rm_blank(activity.xpath(groups[0])),
                           0)
                   == float(groups[1]))

    @add_partial('(\S*) exists (\S*) times?\?')
    def exist_times(activity, groups):
        return len(rm_blank(activity.xpath(groups[0]))) == int(groups[1])

    @add_partial('(\S*) exists more than (\S*) times?\?')
    def exist_times(activity, groups):
        return len(rm_blank(activity.xpath(groups[0]))) > int(groups[1])

    def exist_check(activity, xpath):
        return bool(rm_blank(activity.xpath(xpath)))

    @add_partial('only one of (\S*) or (\S*) exists\?')
    def exist_xor(activity, groups):
        return (exist_check(activity, groups[0]) != 
                exist_check(activity, groups[1]))

    @add_partial('(\S*) or (\S*) exists\?')
    def exist_or(activity, groups):
        return (exist_check(activity, groups[0]) or 
                exist_check(activity, groups[1]))

    @add_partial('(\S*) exists\?') 
    def exist(activity, groups):
        return exist_check(activity, groups[0]) 

    @add('(.*)')
    def fail(line):
        return None


    def get_mappings(ms, line):
        for regex, lam in ms:
            yield regex.match(line), lam

    first_true = lambda tupl: bool(tupl.__getitem__(0))

    test_functions = {}

    tests = itertools.ifilter(lambda test: test.test_level == 1, tests)
    tests = itertools.ifilter(lambda test: not ignore_line(test.name), tests)

    def function_for_test(test):
        line = test.name

        match_data = get_mappings(mappings, line)
        matching_mappings = itertools.ifilter(first_true, match_data)

        try:
            m, lam = matching_mappings.next()
        except StopIteration:
            raise TestSyntaxError(line)

        return lam(m.groups())

    def id_of_test(test): return test.id

    def test_data(test):
        f = function_for_test(test)
        test_id = id_of_test(test)
        return test_id, f

    return dict(itertools.imap(test_data, tests))
