from ops.telemetry import summarize

def events(status,count):
    return [{"status":status,"ready_ms":float(n)} for n in range(count)]

def test_no_data_is_not_healthy():assert summarize([])["alert"]=="insufficient_data"

def test_one_failure_is_insufficient():assert summarize(events(503,1))["alert"]=="insufficient_data"

def test_client_rejections_are_not_server_errors():assert summarize(events(422,20))["alert"]=="ok"

def test_threshold_includes_exact_boundary():assert summarize(events(200,19)+events(503,1))["alert"]=="page"

def test_p95_nearest_rank():assert summarize(events(200,20))["p95_ready_ms"]==18.0
