from unittest import TestCase

from mini_eval import mini_eval


def summation(*args):
    total = 0
    for arg in args: total += arg
    return total;


count = 0


def counter():
    global count
    count += 1
    return count


names = {"abs": abs, "a": 10, "foo": {"bar": 20}, "add": summation, "counter": counter}


class TestMiniEval(TestCase):
    def test_is_string(self):
        # samples
        mini_eval("{1:2,2:3}")
        mini_eval("'a'")
        mini_eval("1")
        mini_eval("+1")
        mini_eval("-1")
        mini_eval("1+2")
        mini_eval("1+2+3")
        mini_eval("1+2*3")
        mini_eval("(1+2)*3")
        mini_eval("()")
        mini_eval("(1)")
        mini_eval("(1,)")
        mini_eval("(1, 2)")
        mini_eval("[1, 2, 3]")
        mini_eval("{}")
        mini_eval("{1: 'one', 2: 'two'}")
        mini_eval("1.0*2+3")
        mini_eval("'hello'+'world'")
        mini_eval("2**3**4")
        mini_eval("1 and 2")
        mini_eval("0 or 2")
        mini_eval("foo.bar")
        mini_eval("1 + a")
        mini_eval("1 if 2 else 3")
        mini_eval("'hello'[0]")
        mini_eval("add()")
        mini_eval("add(1,2,3)")
        mini_eval("True")
        mini_eval("True or False")
        mini_eval("1 in [2, 1]")
        mini_eval("1 not in [2, 1]")
        mini_eval("not True")
        mini_eval("0 not in [1, 2]")
        mini_eval("1 in [1, 2]")
        mini_eval("1 is 2")
        mini_eval("1 is not 2")
        mini_eval("1 is (not 2)")
        mini_eval("[1,2]")
        mini_eval("abs(5)")
        mini_eval("abs(-5)")
        mini_eval("((1))")
        mini_eval("1<2+1<2+1")
        mini_eval("1<2")
        mini_eval("1<2<3<4")
        mini_eval("counter()<counter()<counter()")
