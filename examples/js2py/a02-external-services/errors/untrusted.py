"""Expected failure: parseable JSON is not necessarily trusted application data."""
from service import Hint

Hint.model_validate_json(b'{"priority":"urgent","debug":"synthetic-only"}')
