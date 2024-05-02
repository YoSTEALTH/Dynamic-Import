import conflict


def test_conflict():
    from conflict import my_func, another_func
    assert my_func() == 'my_func() called'
    assert another_func() == 'another_func() called'


def test_multiple_conflict():
    assert conflict.another_func() == 'another_func() called'
    assert conflict.my_func() == 'my_func() called'
    

def test_multiple_conflict2():
    assert conflict.another_func() == 'another_func() called'
    assert conflict.my_func() == 'my_func() called'
