"""Expected startup failure with a deliberately fake credential-shaped URL."""
from app import create_app

create_app("http://demo:NOT_A_REAL_SECRET@127.0.0.1:8766/?token=FAKE")
