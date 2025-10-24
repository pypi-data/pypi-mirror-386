from mareval import compute_auc

def test_auc_range():
    assert 0 <= compute_auc([1, 2, 3], [0, 1, 2]) <= 1
