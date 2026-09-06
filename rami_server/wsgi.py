import os

from flask import jsonify, request

from app import APP, init_schema

MATCH_RESULT_SECRET = os.environ.get("MATCH_RESULT_SECRET", "")


@APP.before_request
def protect_authoritative_match_result():
    # The mobile client must never be able to award itself Elo.
    # Final rankings are accepted only from the future authoritative match host.
    if request.path.startswith("/api/matches/") and request.path.endswith("/finish"):
        if not MATCH_RESULT_SECRET:
            return jsonify(ok=False, error="MATCH_RESULT_SERVER_NOT_CONFIGURED"), 503
        if request.headers.get("X-Rami-Match-Secret", "") != MATCH_RESULT_SECRET:
            return jsonify(ok=False, error="MATCH_RESULT_FORBIDDEN"), 403


init_schema()
