#!/usr/bin/env bash
# scripts/smoke_test.sh
# Manual smoke test for the application running through Docker Compose.
#
# It exercises the full flow against the real API: creates a user, tries to duplicate it,
# creates a linked host, validates error responses and deletes the user (cascade).
# At the end every created record is removed, so the database returns to its initial state.
#
# Usage:
#   ./scripts/smoke_test.sh                 # uses http://localhost:8000
#   API=http://192.168.0.10:8000 ./scripts/smoke_test.sh
set -u

API="${API:-http://localhost:8000}"
SUFFIX="$(date +%s)"
USERNAME="manual_${SUFFIX}"
HOSTNAME="host-manual-${SUFFIX}"

failures=0

check() { # check <description> <expected_status> <actual_status>
    if [ "$2" = "$3" ]; then
        echo "  [PASS] $1 (HTTP $3)"
    else
        echo "  [FAIL] $1 (expected HTTP $2, got $3)"
        failures=$((failures + 1))
    fi
}

status() { curl -s -o "$2" -w '%{http_code}' "${@:3}"; }

echo "=== Target API: $API ==="

echo
echo "1) Endpoint availability"
check "GET /api/users" 200 "$(status '' /tmp/_smoke_out.json "$API/api/users")"
check "GET /api/hosts" 200 "$(status '' /tmp/_smoke_out.json "$API/api/hosts")"
check "GET /docs" 200 "$(status '' /tmp/_smoke_out.json "$API/docs")"

echo
echo "2) User creation (POST /api/users)"
USER_RESPONSE="$(curl -s -X POST "$API/api/users" \
    -H 'Content-Type: application/json' \
    -d "{\"first_name\":\"Manual\",\"last_name\":\"Test\",\"username\":\"$USERNAME\",\"address\":\"1 Test Street\"}")"
echo "  response: $USER_RESPONSE"
USER_ID="$(printf '%s' "$USER_RESPONSE" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

echo
echo "3) User business rules"
check "POST duplicated username" 400 "$(status '' /tmp/_smoke_dup.json -X POST "$API/api/users" \
    -H 'Content-Type: application/json' \
    -d "{\"first_name\":\"Other\",\"last_name\":\"Test\",\"username\":\"$USERNAME\",\"address\":\"2 Test Street\"}")"
echo "  detail: $(cat /tmp/_smoke_dup.json)"
check "POST without 'username' (validation)" 422 "$(status '' /tmp/_smoke_422.json -X POST "$API/api/users" \
    -H 'Content-Type: application/json' -d '{"first_name":"No","last_name":"Username","address":"3 Test Street"}')"

echo
echo "4) Linked host creation (POST /api/hosts, user_id=$USER_ID)"
HOST_RESPONSE="$(curl -s -X POST "$API/api/hosts" -H 'Content-Type: application/json' \
    -d "{\"hostname\":\"$HOSTNAME\",\"manufacturer\":\"Dell\",\"model\":\"R740\",\"cpu\":\"Xeon\",\
\"cpu_count\":2,\"ram\":\"32GB\",\"disk\":\"1TB\",\"storage_type\":\"SSD\",\"interfaces\":\"Ethernet\",\
\"ips\":\"10.0.0.99\",\"location\":\"Manual Room\",\"user_id\":$USER_ID}")"
echo "  response: $HOST_RESPONSE"
HOST_ID="$(printf '%s' "$HOST_RESPONSE" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

echo
echo "5) User -> Hosts relationship"
curl -s "$API/api/users/$USER_ID" | python3 -m json.tool | sed 's/^/  /'

echo
echo "6) Expected errors"
check "POST host with unknown user_id" 404 "$(status '' /tmp/_smoke_404.json -X POST "$API/api/hosts" \
    -H 'Content-Type: application/json' \
    -d '{"hostname":"h","manufacturer":"D","model":"M","cpu":"C","cpu_count":1,"ram":"1GB","disk":"1TB","storage_type":"SSD","interfaces":"Eth","ips":"10.0.0.1","location":"Room","user_id":999999}')"
echo "  detail: $(cat /tmp/_smoke_404.json)"
check "GET unknown user" 404 "$(status '' /tmp/_smoke_out.json "$API/api/users/999999")"
check "DELETE unknown host" 404 "$(status '' /tmp/_smoke_out.json -X DELETE "$API/api/hosts/999999")"

echo
echo "7) Cascade deletion (DELETE /api/users/$USER_ID)"
curl -s -X DELETE "$API/api/users/$USER_ID" | sed 's/^/  /'
echo
check "GET deleted user" 404 "$(status '' /tmp/_smoke_out.json "$API/api/users/$USER_ID")"
# Note: the API does not expose GET /api/hosts/{id}, so the cascade is checked in the list.
REMAINING_HOSTS="$(curl -s "$API/api/hosts" \
    | python3 -c "import json,sys; print(sum(1 for h in json.load(sys.stdin) if h['id'] == $HOST_ID))")"
if [ "$REMAINING_HOSTS" = "0" ]; then
    echo "  [PASS] host removed in cascade (0 matches in GET /api/hosts)"
else
    echo "  [FAIL] host still exists after the cascade ($REMAINING_HOSTS match(es))"
    failures=$((failures + 1))
fi

echo
if [ "$failures" -eq 0 ]; then
    echo "=== Every step passed ==="
else
    echo "=== $failures step(s) failed ==="
fi
exit "$failures"
