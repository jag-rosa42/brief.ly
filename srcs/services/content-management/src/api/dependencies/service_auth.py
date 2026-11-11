"""The service token checks of the /internal routes (ADR-0008).

Each route says which scope it needs, as in docs/api/04_content-management.md.
Per route, not per router: the GET and PUT routes of one router need
different scopes (reading articles vs writing summaries).

A request without a valid service token gets 401; one whose token lacks the
scope gets 403 INSUFFICIENT_SCOPE (shared_auth's handlers).
"""

from fastapi import Depends
from shared_auth import require_service_scopes

TOPICS_READ = Depends(require_service_scopes("topics:read"))
ARTICLES_READ = Depends(require_service_scopes("articles:read"))
SUMMARIES_WRITE = Depends(require_service_scopes("summaries:write"))
