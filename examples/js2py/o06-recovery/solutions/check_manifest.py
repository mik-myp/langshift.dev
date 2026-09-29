import math

REQUIRED={"users","projects","project_members","tasks","auth_sessions","task_operations","alembic_version"}

def verify_manifest(manifest,now,max_age):
    if type(max_age) not in (int,float) or not math.isfinite(max_age) or max_age<0:raise ValueError("invalid maximum age")
    if any(type(value) not in (int,float) or not math.isfinite(value) for value in [now,manifest["created_at"]]):raise ValueError("invalid time")
    if manifest["created_at"]>now or now-manifest["created_at"]>max_age:raise ValueError("snapshot outside approved age")
    if set(manifest["tables"])!=REQUIRED:raise ValueError("incomplete backup inventory")
    if type(manifest["bytes"]) is not int or manifest["bytes"]<=0:raise ValueError("empty archive")
    return True
