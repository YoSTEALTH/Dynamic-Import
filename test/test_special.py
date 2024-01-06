import pytest
from dynamic_import.special import special


def test_special():
    my_list = ['first', '__name__', '_name', 'name_', 'name', 'name__', '__name', '___name___', '', 'last']
    result = ('first', '_name', 'name_', 'name', 'name__', '__name', '___name___', '', 'last')
    assert tuple(special(my_list)) == result

    with pytest.raises(ValueError):
        [_ for _ in special(my_list, error=True)]
