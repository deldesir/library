import pytest
from tests.utils import connect_db_args
from xklb.lb import library as lb

def test_lb_row_add_success(temp_db):
    db1 = temp_db()
    lb(['row-add', db1, '--test_b', '1', '--test-a', '2'])

    args = connect_db_args(db1)
    result= list(args.db.query('select * from media'))

    assert result == [{'test_b': 1, 'test_a': 2}]

def test_lb_row_add_missing_arguments(temp_db):
    db1 = temp_db()
    with pytest.raises(SystemExit):
        lb(['row-add', db1])
