#!/bin/bash
# HexaNote API Verification Script (Bash version)
# Tests all API endpoints from authentication to chat/sync operations.

set -e  # Exit on error

# Configuration
BASE_URL="http://localhost:8001/api/v1"
PASSWORD="hexanote"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables
TOKEN=""
DEVICE_ID=""
SESSION_ID=""
NOTE_ID=""
TEST_COUNT=0
PASS_COUNT=0
FAIL_COUNT=0

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    ((PASS_COUNT++))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ((FAIL_COUNT++))
}

log_test() {
    ((TEST_COUNT++))
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}TEST $TEST_COUNT: $1${NC}"
    echo -e "${YELLOW}========================================${NC}"
}

# Make API request
api_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local extra_args=${4:-""}

    local url="${BASE_URL}${endpoint}"
    local headers=(-H "Content-Type: application/json")

    # Add auth token if available
    if [ -n "$TOKEN" ]; then
        headers+=(-H "Authorization: Bearer $TOKEN")
    fi

    log_info "$method $endpoint"

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "${headers[@]}" $extra_args "$url")
    else
        if [ -n "$data" ]; then
            response=$(curl -s -w "\n%{http_code}" -X "$method" "${headers[@]}" -d "$data" $extra_args "$url")
        else
            response=$(curl -s -w "\n%{http_code}" -X "$method" "${headers[@]}" $extra_args "$url")
        fi
    fi

    # Parse response
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    echo "$body" | jq '.' 2>/dev/null || echo "$body"

    if [[ "$http_code" =~ ^(200|201|204)$ ]]; then
        log_success "✓ Status $http_code"
        echo "$body"
        return 0
    else
        log_error "✗ Status $http_code"
        return 1
    fi
}

# ===========================
# TEST FUNCTIONS
# ===========================

test_health_check() {
    log_test "Health Check"
    if response=$(api_request "GET" "/health"); then
        echo "$response" | jq -r '.status'
        return 0
    fi
    return 1
}

test_get_token() {
    log_test "Get Authentication Token"
    local data="{\"password\": \"$PASSWORD\"}"

    if response=$(api_request "POST" "/token" "$data"); then
        TOKEN=$(echo "$response" | jq -r '.access_token')
        log_success "Token obtained: ${TOKEN:0:50}..."
        echo "$response" | jq -r '.expires_in' | xargs -I {} echo "Expires in: {} seconds"
        return 0
    fi
    return 1
}

test_register_device() {
    log_test "Register Device"
    local data='{"device_name": "Test Device Bash", "device_type": "windows"}'

    if response=$(api_request "POST" "/devices/register" "$data"); then
        DEVICE_ID=$(echo "$response" | jq -r '.device_id')
        log_success "Device ID: $DEVICE_ID"
        return 0
    fi
    return 1
}

test_create_note() {
    log_test "Create Note"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local data=$(cat <<EOF
{
    "title": "Test Note - Bash Script",
    "content": "# API Test Note (Bash)\\n\\nCreated by bash verification script.\\n\\nTimestamp: $timestamp",
    "tags": ["test", "bash", "api"]
}
EOF
)

    if response=$(api_request "POST" "/notes" "$data"); then
        NOTE_ID=$(echo "$response" | jq -r '.id')
        log_success "Note created: $NOTE_ID"
        return 0
    fi
    return 1
}

test_list_notes() {
    log_test "List Notes"
    if response=$(api_request "GET" "/notes?page=1&limit=10"); then
        total=$(echo "$response" | jq -r '.total')
        count=$(echo "$response" | jq -r '.notes | length')
        log_success "Total notes: $total, Retrieved: $count"
        return 0
    fi
    return 1
}

test_get_note() {
    log_test "Get Note by ID"
    if [ -z "$NOTE_ID" ]; then
        log_error "No note ID available"
        return 1
    fi

    if response=$(api_request "GET" "/notes/$NOTE_ID"); then
        title=$(echo "$response" | jq -r '.title')
        log_success "Retrieved: $title"
        return 0
    fi
    return 1
}

test_update_note() {
    log_test "Update Note"
    if [ -z "$NOTE_ID" ]; then
        log_error "No note ID available"
        return 1
    fi

    # Get current version
    current=$(api_request "GET" "/notes/$NOTE_ID")
    version=$(echo "$current" | jq -r '.version')

    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local data=$(cat <<EOF
{
    "title": "Test Note - UPDATED (Bash)",
    "content": "# Updated API Test Note\\n\\n**Updated** by bash script.\\n\\nUpdate: $timestamp",
    "tags": ["test", "bash", "api", "updated"],
    "version": $version
}
EOF
)

    if response=$(api_request "PUT" "/notes/$NOTE_ID" "$data"); then
        new_version=$(echo "$response" | jq -r '.version')
        log_success "Updated to version $new_version"
        return 0
    fi
    return 1
}

test_list_tags() {
    log_test "List Tags"
    if response=$(api_request "GET" "/notes/tags"); then
        count=$(echo "$response" | jq -r '.tags | length')
        log_success "Total unique tags: $count"
        echo "$response" | jq -r '.tags[:5][] | "  - \(.tag): \(.count)"'
        return 0
    fi
    return 1
}

test_semantic_search() {
    log_test "Semantic Search"
    log_info "Waiting 2 seconds for Weaviate indexing..."
    sleep 2

    if response=$(api_request "GET" "/notes/search/semantic?q=test%20bash&limit=5"); then
        count=$(echo "$response" | jq -r '.results | length')
        log_success "Found $count results"
        echo "$response" | jq -r '.results[:3][] | "  - \(.title) (score: \(.relevance_score))"'
        return 0
    fi
    return 1
}

test_search_within_note() {
    log_test "Search Within Note"
    if [ -z "$NOTE_ID" ]; then
        log_error "No note ID available"
        return 1
    fi

    if response=$(api_request "GET" "/notes/$NOTE_ID/search?q=bash&window=2"); then
        chunk_range=$(echo "$response" | jq -r '.chunk_range')
        log_success "Best match in chunks $chunk_range"
        return 0
    fi
    return 1
}

test_reindex_notes() {
    log_test "Reindex Notes"
    if response=$(api_request "POST" "/notes/reindex"); then
        total=$(echo "$response" | jq -r '.total')
        success=$(echo "$response" | jq -r '.success')
        errors=$(echo "$response" | jq -r '.errors')
        log_success "Indexed $success/$total notes (errors: $errors)"
        return 0
    fi
    return 1
}

test_create_chat_session() {
    log_test "Create Chat Session"
    if response=$(api_request "POST" "/chat/sessions"); then
        SESSION_ID=$(echo "$response" | jq -r '.session_id')
        log_success "Session: $SESSION_ID"
        return 0
    fi
    return 1
}

test_chat_query() {
    log_test "Chat Query"
    local data=$(cat <<EOF
{
    "message": "What test notes do I have?",
    "session_id": "$SESSION_ID",
    "limit": 3
}
EOF
)

    if response=$(api_request "POST" "/chat/query" "$data"); then
        message=$(echo "$response" | jq -r '.message' | head -c 200)
        context_count=$(echo "$response" | jq -r '.context_notes | length')
        log_success "AI responded with $context_count context notes"
        echo "Response preview: $message..."
        return 0
    fi
    return 1
}

test_chat_history() {
    log_test "Get Chat History"
    if [ -z "$SESSION_ID" ]; then
        log_error "No session ID available"
        return 1
    fi

    if response=$(api_request "GET" "/chat/history?session_id=$SESSION_ID&limit=50"); then
        count=$(echo "$response" | jq -r '.messages | length')
        log_success "Retrieved $count messages"
        return 0
    fi
    return 1
}

test_sync_notes() {
    log_test "Sync Notes"
    if [ -z "$DEVICE_ID" ]; then
        log_error "No device ID available"
        return 1
    fi

    local data=$(cat <<EOF
{
    "device_id": "$DEVICE_ID",
    "last_sync_timestamp": "2026-01-01T00:00:00Z",
    "notes": []
}
EOF
)

    if response=$(api_request "POST" "/sync" "$data"); then
        update_count=$(echo "$response" | jq -r '.notes_to_update | length')
        delete_count=$(echo "$response" | jq -r '.notes_to_delete | length')
        conflict_count=$(echo "$response" | jq -r '.conflicts | length')
        log_success "Updates: $update_count, Deletes: $delete_count, Conflicts: $conflict_count"
        return 0
    fi
    return 1
}

test_delete_note() {
    log_test "Delete Note (Cleanup)"
    if [ -z "$NOTE_ID" ]; then
        log_info "No note to delete"
        log_success "Skip"
        return 0
    fi

    if api_request "DELETE" "/notes/$NOTE_ID"; then
        log_success "Note deleted: $NOTE_ID"
        return 0
    fi
    return 1
}

# ===========================
# MAIN EXECUTION
# ===========================

print_banner() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  HEXANOTE API VERIFICATION SCRIPT (BASH)${NC}"
    echo -e "${BLUE}  Target: $BASE_URL${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
}

print_summary() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  TEST SUMMARY${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo -e "Total Tests: $TEST_COUNT"
    echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
    echo -e "${RED}Failed: $FAIL_COUNT${NC}"
    echo ""

    if [ $FAIL_COUNT -eq 0 ]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED! 🎉${NC}"
    else
        echo -e "${RED}⚠️  $FAIL_COUNT test(s) failed${NC}"
    fi
    echo ""
}

main() {
    # Check dependencies
    command -v curl >/dev/null 2>&1 || { log_error "curl is required but not installed. Aborting."; exit 1; }
    command -v jq >/dev/null 2>&1 || { log_error "jq is required but not installed. Aborting."; exit 1; }

    print_banner

    # Run all tests
    test_health_check || true
    test_get_token || { log_error "Authentication failed. Cannot continue."; exit 1; }
    test_register_device || true
    test_create_note || true
    test_list_notes || true
    test_get_note || true
    test_update_note || true
    test_list_tags || true
    test_semantic_search || true
    test_search_within_note || true
    test_reindex_notes || true
    test_create_chat_session || true
    test_chat_query || true
    test_chat_history || true
    test_sync_notes || true
    test_delete_note || true

    print_summary

    # Exit with appropriate code
    if [ $FAIL_COUNT -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

main "$@"
