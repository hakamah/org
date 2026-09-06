import math
import os
from datetime import datetime, timezone, timedelta
from functools import wraps

import jwt
import psycopg
from flask import Flask, jsonify, request
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

APP = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL", "")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_TTL_DAYS = int(os.environ.get("JWT_TTL_DAYS", "30"))
ELO_K = 32.0
START_ELO = 100


def db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg.connect(DATABASE_URL, autocommit=False)


def init_schema():
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = f.read()
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(schema)
        conn.commit()


def token_for(account_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(account_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=JWT_TTL_DAYS)).timestamp()),
        "iss": "rami-auth-server",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def require_auth(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify(ok=False, error="AUTH_REQUIRED"), 401
        try:
            payload = jwt.decode(auth[7:], JWT_SECRET, algorithms=["HS256"], issuer="rami-auth-server")
            request.account_id = int(payload["sub"])
        except Exception:
            return jsonify(ok=False, error="INVALID_TOKEN"), 401
        return fn(*args, **kwargs)
    return wrapped


def account_payload(cur, account_id: int):
    cur.execute("""
        SELECT id, display_name, elo, games_played, wins
        FROM rami_accounts WHERE id=%s
    """, (account_id,))
    row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row[0], "display_name": row[1], "elo": row[2],
        "games_played": row[3], "wins": row[4]
    }


def room_payload(cur, room_id: int):
    cur.execute("""
        SELECT r.id, r.creator_account_id, r.target_players, r.base_elo, r.status,
               COUNT(rp.account_id) AS player_count
        FROM rami_rooms r
        LEFT JOIN rami_room_players rp ON rp.room_id=r.id
        WHERE r.id=%s
        GROUP BY r.id
    """, (room_id,))
    row = cur.fetchone()
    if not row:
        return None
    cur.execute("""
        SELECT rp.seat_index, a.id, a.display_name, a.elo
        FROM rami_room_players rp
        JOIN rami_accounts a ON a.id=rp.account_id
        WHERE rp.room_id=%s ORDER BY rp.seat_index
    """, (room_id,))
    players = [
        {"seat": x[0], "account_id": x[1], "display_name": x[2], "elo": x[3]}
        for x in cur.fetchall()
    ]
    return {
        "id": row[0], "creator_account_id": row[1], "target_players": row[2],
        "base_elo": row[3], "status": row[4], "player_count": row[5],
        "players": players,
    }


def leave_open_rooms(cur, account_id: int):
    cur.execute("""
        SELECT rp.room_id FROM rami_room_players rp
        JOIN rami_rooms r ON r.id=rp.room_id
        WHERE rp.account_id=%s AND r.status='open'
    """, (account_id,))
    room_ids = [r[0] for r in cur.fetchall()]
    for room_id in room_ids:
        cur.execute("SELECT creator_account_id FROM rami_rooms WHERE id=%s FOR UPDATE", (room_id,))
        creator = cur.fetchone()[0]
        cur.execute("DELETE FROM rami_room_players WHERE room_id=%s AND account_id=%s", (room_id, account_id))
        if creator == account_id:
            cur.execute("UPDATE rami_rooms SET status='cancelled' WHERE id=%s AND status='open'", (room_id,))
        else:
            cur.execute("""
                SELECT account_id FROM rami_room_players
                WHERE room_id=%s ORDER BY seat_index LIMIT 1
            """, (room_id,))
            survivor = cur.fetchone()
            if survivor:
                cur.execute("UPDATE rami_rooms SET creator_account_id=%s WHERE id=%s", (survivor[0], room_id))


def start_match_if_full(cur, room_id: int):
    cur.execute("SELECT target_players, status FROM rami_rooms WHERE id=%s FOR UPDATE", (room_id,))
    row = cur.fetchone()
    if not row or row[1] != "open":
        return None
    target = row[0]
    cur.execute("SELECT COUNT(*) FROM rami_room_players WHERE room_id=%s", (room_id,))
    count = cur.fetchone()[0]
    if count < target:
        return None
    cur.execute("UPDATE rami_rooms SET status='started', started_at=NOW() WHERE id=%s", (room_id,))
    cur.execute("INSERT INTO rami_matches(room_id,target_players,status) VALUES(%s,%s,'active') RETURNING id", (room_id, target))
    match_id = cur.fetchone()[0]
    cur.execute("""
        SELECT rp.account_id, rp.seat_index, a.elo
        FROM rami_room_players rp JOIN rami_accounts a ON a.id=rp.account_id
        WHERE rp.room_id=%s ORDER BY rp.seat_index
    """, (room_id,))
    for account_id, seat, elo in cur.fetchall():
        cur.execute("""
            INSERT INTO rami_match_players(match_id,account_id,seat_index,elo_before)
            VALUES(%s,%s,%s,%s)
        """, (match_id, account_id, seat, elo))
    return match_id


def expected_score(rating_a: int, rating_b: int) -> float:
    return 1.0 / (1.0 + math.pow(10.0, (rating_b - rating_a) / 400.0))


def calculate_multiplayer_elo(players):
    # Every placement is treated as virtual pairwise Elo confrontations.
    # Deltas are averaged across opponents so K=32 remains the per-match scale.
    result = {}
    n = len(players)
    for a in players:
        actual_sum = 0.0
        expected_sum = 0.0
        for b in players:
            if a["account_id"] == b["account_id"]:
                continue
            if a["placement"] < b["placement"]:
                actual = 1.0
            elif a["placement"] > b["placement"]:
                actual = 0.0
            else:
                actual = 0.5
            actual_sum += actual
            expected_sum += expected_score(a["elo_before"], b["elo_before"])
        divisor = max(1, n - 1)
        delta = int(round(ELO_K * ((actual_sum - expected_sum) / divisor)))
        new_elo = max(0, a["elo_before"] + delta)
        result[a["account_id"]] = {"delta": new_elo - a["elo_before"], "elo_after": new_elo}
    return result


@APP.get("/health")
def health():
    return jsonify(ok=True, service="rami-auth-server")


@APP.post("/api/auth/google")
def auth_google():
    body = request.get_json(silent=True) or {}
    raw_id_token = str(body.get("id_token", ""))
    if not raw_id_token:
        return jsonify(ok=False, error="MISSING_ID_TOKEN"), 400
    if not GOOGLE_CLIENT_ID or not JWT_SECRET:
        return jsonify(ok=False, error="SERVER_AUTH_NOT_CONFIGURED"), 503
    try:
        claims = id_token.verify_oauth2_token(raw_id_token, google_requests.Request(), GOOGLE_CLIENT_ID)
    except Exception:
        return jsonify(ok=False, error="GOOGLE_TOKEN_INVALID"), 401
    if claims.get("aud") != GOOGLE_CLIENT_ID:
        return jsonify(ok=False, error="GOOGLE_AUDIENCE_INVALID"), 401
    google_sub = str(claims["sub"])
    email = str(claims.get("email", ""))
    name = str(claims.get("name", "Joueur"))[:40] or "Joueur"
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO rami_accounts(google_sub,email,display_name,elo)
                VALUES(%s,%s,%s,%s)
                ON CONFLICT(google_sub) DO UPDATE
                  SET email=EXCLUDED.email, display_name=EXCLUDED.display_name, updated_at=NOW()
                RETURNING id
            """, (google_sub, email, name, START_ELO))
            account_id = cur.fetchone()[0]
            account = account_payload(cur, account_id)
        conn.commit()
    return jsonify(ok=True, token=token_for(account_id), account=account)


@APP.get("/api/me")
@require_auth
def me():
    with db() as conn:
        with conn.cursor() as cur:
            account = account_payload(cur, request.account_id)
    return jsonify(ok=True, account=account)


@APP.post("/api/matchmaking/create")
@require_auth
def create_room():
    body = request.get_json(silent=True) or {}
    target = int(body.get("players", 0))
    if target not in (2, 3, 4):
        return jsonify(ok=False, error="PLAYERS_MUST_BE_2_3_OR_4"), 400
    with db() as conn:
        with conn.cursor() as cur:
            leave_open_rooms(cur, request.account_id)
            cur.execute("SELECT elo FROM rami_accounts WHERE id=%s FOR UPDATE", (request.account_id,))
            row = cur.fetchone()
            if not row:
                return jsonify(ok=False, error="ACCOUNT_NOT_FOUND"), 404
            base_elo = row[0]
            cur.execute("""
                INSERT INTO rami_rooms(creator_account_id,target_players,base_elo,status)
                VALUES(%s,%s,%s,'open') RETURNING id
            """, (request.account_id, target, base_elo))
            room_id = cur.fetchone()[0]
            cur.execute("INSERT INTO rami_room_players(room_id,account_id,seat_index) VALUES(%s,%s,0)", (room_id, request.account_id))
            room = room_payload(cur, room_id)
        conn.commit()
    return jsonify(ok=True, room=room)


@APP.post("/api/matchmaking/search")
@require_auth
def search_room():
    body = request.get_json(silent=True) or {}
    target = int(body.get("players", 0))
    if target not in (2, 3, 4):
        return jsonify(ok=False, error="PLAYERS_MUST_BE_2_3_OR_4"), 400
    with db() as conn:
        with conn.cursor() as cur:
            leave_open_rooms(cur, request.account_id)
            cur.execute("SELECT elo FROM rami_accounts WHERE id=%s FOR UPDATE", (request.account_id,))
            row = cur.fetchone()
            if not row:
                return jsonify(ok=False, error="ACCOUNT_NOT_FOUND"), 404
            player_elo = row[0]
            # base_elo is frozen at room creation; it is never averaged with joiners.
            cur.execute("""
                SELECT r.id
                FROM rami_rooms r
                WHERE r.status='open' AND r.target_players=%s
                  AND r.creator_account_id<>%s
                  AND (SELECT COUNT(*) FROM rami_room_players rp WHERE rp.room_id=r.id) < r.target_players
                ORDER BY ABS(r.base_elo-%s) ASC, r.created_at ASC
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            """, (target, request.account_id, player_elo))
            found = cur.fetchone()
            created = False
            if found:
                room_id = found[0]
                cur.execute("SELECT COALESCE(MAX(seat_index),-1)+1 FROM rami_room_players WHERE room_id=%s", (room_id,))
                seat = cur.fetchone()[0]
                cur.execute("INSERT INTO rami_room_players(room_id,account_id,seat_index) VALUES(%s,%s,%s)", (room_id, request.account_id, seat))
            else:
                created = True
                cur.execute("""
                    INSERT INTO rami_rooms(creator_account_id,target_players,base_elo,status)
                    VALUES(%s,%s,%s,'open') RETURNING id
                """, (request.account_id, target, player_elo))
                room_id = cur.fetchone()[0]
                cur.execute("INSERT INTO rami_room_players(room_id,account_id,seat_index) VALUES(%s,%s,0)", (room_id, request.account_id))
            match_id = start_match_if_full(cur, room_id)
            room = room_payload(cur, room_id)
        conn.commit()
    return jsonify(ok=True, created=created, room=room, match_id=match_id)


@APP.get("/api/matchmaking/room/<int:room_id>")
@require_auth
def get_room(room_id):
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM rami_room_players WHERE room_id=%s AND account_id=%s", (room_id, request.account_id))
            if not cur.fetchone():
                return jsonify(ok=False, error="NOT_IN_ROOM"), 403
            room = room_payload(cur, room_id)
            cur.execute("SELECT id FROM rami_matches WHERE room_id=%s AND status='active'", (room_id,))
            match = cur.fetchone()
    return jsonify(ok=True, room=room, match_id=(match[0] if match else None))


@APP.post("/api/matchmaking/leave")
@require_auth
def leave_room():
    with db() as conn:
        with conn.cursor() as cur:
            leave_open_rooms(cur, request.account_id)
        conn.commit()
    return jsonify(ok=True)


@APP.post("/api/matches/<int:match_id>/disconnect")
@require_auth
def disconnect_match(match_id):
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE rami_match_players SET disconnected=TRUE
                WHERE match_id=%s AND account_id=%s
            """, (match_id, request.account_id))
            if cur.rowcount == 0:
                return jsonify(ok=False, error="NOT_IN_MATCH"), 403
        conn.commit()
    return jsonify(ok=True)


@APP.post("/api/matches/<int:match_id>/finish")
@require_auth
def finish_match(match_id):
    # Foundation endpoint: in production gameplay the authoritative match host/server
    # should call this with a service credential. Until networked gameplay is wired,
    # only participants can submit and the first valid final ranking wins atomically.
    body = request.get_json(silent=True) or {}
    placements = body.get("placements", [])
    if not isinstance(placements, list):
        return jsonify(ok=False, error="INVALID_PLACEMENTS"), 400
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT status,target_players FROM rami_matches WHERE id=%s FOR UPDATE", (match_id,))
            match = cur.fetchone()
            if not match:
                return jsonify(ok=False, error="MATCH_NOT_FOUND"), 404
            if match[0] != "active":
                return jsonify(ok=False, error="MATCH_ALREADY_FINISHED"), 409
            cur.execute("SELECT 1 FROM rami_match_players WHERE match_id=%s AND account_id=%s", (match_id, request.account_id))
            if not cur.fetchone():
                return jsonify(ok=False, error="NOT_IN_MATCH"), 403
            cur.execute("SELECT account_id,elo_before,disconnected FROM rami_match_players WHERE match_id=%s", (match_id,))
            rows = cur.fetchall()
            ids = {r[0] for r in rows}
            submitted = {int(x["account_id"]): int(x["placement"]) for x in placements if isinstance(x, dict)}
            if set(submitted.keys()) != ids or sorted(submitted.values()) != list(range(1, len(ids)+1)):
                return jsonify(ok=False, error="PLACEMENTS_MUST_COVER_ALL_PLAYERS"), 400
            # A disconnected player is always forced to the worst available placement.
            disconnected_ids = [r[0] for r in rows if r[2]]
            if disconnected_ids:
                worst = len(ids)
                for did in disconnected_ids:
                    current_holder = next((aid for aid,p in submitted.items() if p == worst), None)
                    old = submitted[did]
                    submitted[did] = worst
                    if current_holder is not None and current_holder != did:
                        submitted[current_holder] = old
            players = [{"account_id": r[0], "elo_before": r[1], "placement": submitted[r[0]]} for r in rows]
            updates = calculate_multiplayer_elo(players)
            winner_id = min(players, key=lambda x: x["placement"])["account_id"]
            for p in players:
                upd = updates[p["account_id"]]
                cur.execute("""
                    UPDATE rami_match_players SET placement=%s, elo_after=%s
                    WHERE match_id=%s AND account_id=%s
                """, (p["placement"], upd["elo_after"], match_id, p["account_id"]))
                cur.execute("""
                    UPDATE rami_accounts
                    SET elo=%s, games_played=games_played+1,
                        wins=wins + CASE WHEN id=%s THEN 1 ELSE 0 END,
                        updated_at=NOW()
                    WHERE id=%s
                """, (upd["elo_after"], winner_id, p["account_id"]))
            cur.execute("UPDATE rami_matches SET status='finished',finished_at=NOW() WHERE id=%s", (match_id,))
        conn.commit()
    return jsonify(ok=True, elo={str(k): v for k,v in updates.items()})


if __name__ == "__main__":
    init_schema()
    APP.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
