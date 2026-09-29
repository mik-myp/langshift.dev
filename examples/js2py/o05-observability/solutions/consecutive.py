def sustained_alert(windows):
    # Two consecutive adequately sampled unhealthy windows; insufficient breaks the run.
    streak=0
    for window in windows:
        unhealthy=window["requests"]>=20 and window["error_rate"]>=.05
        streak=streak+1 if unhealthy else 0
        if streak>=2:return True
    return False
