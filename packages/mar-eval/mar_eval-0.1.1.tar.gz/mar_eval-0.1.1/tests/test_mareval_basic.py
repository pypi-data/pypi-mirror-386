from mareval import compute_auc

def test_auc_range():
    labels = [0, 1, 0, 1]
    decision_values = [0.1, 0.9, 0.4, 0.8]
    result = compute_auc(decision_values, labels)
    auc = result["auc"]

    # Check that AUC is between 0 and 1
    assert 0 <= auc <= 1
    # Check that CI is a tuple of two floats
    assert isinstance(result["ci"], tuple)
    assert len(result["ci"]) == 2