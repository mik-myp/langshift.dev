from solutions.consecutive import sustained_alert

def test_requires_consecutive_samples():
    bad={"requests":20,"error_rate":.1};small={"requests":1,"error_rate":1};good={"requests":20,"error_rate":0}
    assert sustained_alert([bad,bad])
    assert not sustained_alert([bad,small,bad])
    assert not sustained_alert([bad,good,bad])
    assert not sustained_alert([])
