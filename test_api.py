#!/usr/bin/env python3
"""
HexaNote API Verification Script
Tests all API endpoints from authentication to chat/sync operations.
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Optional, Dict, Any

# Configuration
BASE_URL = "http://localhost:8001/api/v1"
PASSWORD = "hexanote"

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class APITester:
    def __init__(self, base_url: str, password: str):
        self.base_url = base_url
        self.password = password
        self.token: Optional[str] = None
        self.device_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.test_note_id: Optional[str] = None
        self.test_results = []

    def log(self, message: str, level: str = "INFO"):
        """Log formatted message."""
        colors = {
            "INFO": BLUE,
            "SUCCESS": GREEN,
            "ERROR": RED,
            "WARNING": YELLOW
        }
        color = colors.get(level, RESET)
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] [{level}] {message}{RESET}")

    def record_test(self, test_name: str, success: bool, details: str = ""):
        """Record test result."""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })

    def make_request(self, method: str, endpoint: str, **kwargs) -> tuple[bool, Any]:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.get('headers', {})

        # Add auth token if available
        if self.token and 'Authorization' not in headers:
            headers['Authorization'] = f"Bearer {self.token}"

        kwargs['headers'] = headers

        try:
            response = requests.request(method, url, **kwargs)

            # Log request
            self.log(f"{method} {endpoint}", "INFO")

            # Try to parse JSON response
            try:
                data = response.json()
            except:
                data = response.text

            # Check if successful
            if response.status_code in [200, 201, 204]:
                self.log(f"✓ Status {response.status_code}", "SUCCESS")
                return True, data
            else:
                self.log(f"✗ Status {response.status_code}: {data}", "ERROR")
                return False, data

        except requests.exceptions.RequestException as e:
            self.log(f"✗ Request failed: {str(e)}", "ERROR")
            return False, str(e)

    def print_json(self, data: Any, indent: int = 2):
        """Pretty print JSON data."""
        print(json.dumps(data, indent=indent))

    # ===========================
    # AUTHENTICATION TESTS
    # ===========================

    def test_health_check(self) -> bool:
        """Test health check endpoint (no auth required)."""
        self.log("=" * 60, "INFO")
        self.log("TEST: Health Check", "INFO")
        self.log("=" * 60, "INFO")

        success, data = self.make_request("GET", "/health")

        if success:
            self.log(f"Health Status: {data.get('status')}", "SUCCESS")
            self.log(f"Services: {data.get('services')}", "SUCCESS")
            self.print_json(data)

        self.record_test("Health Check", success)
        return success

    def test_get_token(self) -> bool:
        """Test authentication and get token."""
        self.log("=" * 60, "INFO")
        self.log("TEST: Get Authentication Token", "INFO")
        self.log("=" * 60, "INFO")

        success, data = self.make_request(
            "POST",
            "/token",
            json={"password": self.password}
        )

        if success:
            self.token = data.get('access_token')
            self.log(f"Token obtained: {self.token[:50]}...", "SUCCESS")
            self.log(f"Expires in: {data.get('expires_in')} seconds", "SUCCESS")
            self.print_json(data)

        self.record_test("Get Token", success)
        return success

    def test_register_device(self) -> bool:
        """Test device registration."""
        self.log("=" * 60, "INFO")
        self.log("TEST: Register Device", "INFO")
        self.log("=" * 60, "INFO")

        success, data = self.make_request(
            "POST",
            "/devices/register",
            json={
                "device_name": "Test Device",
                "device_type": "windows"
            }
        )

        if success:
            self.device_id = data.get('device_id')
            self.log(f"Device ID: {self.device_id}", "SUCCESS")
            self.print_json(data)

        self.record_test("Register Device", success)
        return success

    # ===========================
    # NOTES CRUD TESTS
    # ===========================

    def test_create_note(self) -> bool:
        """Test creating a new note."""
        self.log("=" * 60, "INFO")
        self.log("TEST: Create Note", "INFO")
        self.log("=" * 60, "INFO")

        note_data = {
            "title": "Test Note - API Verification",
            "content": "# API Test Note\n\nThis note was created by the API verification script.\n\n## Features Tested\n- Authentication\n- CRUD operations\n- Search\n- Chat",
            "tags": ["test", "api", "verification"]
        }

        success, data = self.make_request(
            "POST",
            "/notes",
            json=note_data
        )

        if success:
            self.test_note_id = data.get('id')
            self.log(f"Note created with ID: {self.test_note_id}", "SUCCESS")
            self.print_json(data)

        self.record_test("Create Note", success)
        return success

    def test_list_notes(self) -> bool:
        """Test listing notes with pagination."""
        self.log("=" * 60, "INFO")
        self.log("TEST: List Notes", "INFO")
        self.log("=" * 60, "INFO")

        success, data = self.make_request(
            "GET",
            "/notes",
            params={"page": 1, "limit": 10}
        )

        if success:
            self.log(f"Total notes: {data.get('total')}", "SUCCESS")
            self.log(f"Retrieved: {len(data.get('notes', []))} notes", "SUCCESS")
            self.print_json(data)

        self.record_test("List Notes", success)
        return success

    def test_get_note(self) -> bool:
        """Test getting a specific note by ID."""
        self.log("=" * 60, "INFO")
        self.log("TEST: Get Note by ID", "INFO")
        self.log("=" * 60, "INFO")

        if not self.test_note_id:
            self.log("No test note ID available", "ERROR")
            self.record_test("Get Note", False, "No note ID")
            return False

        success, data = self.make_request(
            "GET",
            f"/notes/{self.test_note_id}"
        )

        if success:
            self.log(f"Retrieved note: {data.get('title')}", "SUCCESS")
            self.print_json(data)

        self.record_test("Get Note", success)
        return success

    def test_update_note(self) -> bool:
        """Test updating an existing note."""
        self.log("=" * 60, "INFO")
        self.log("TEST: Update Note", "INFO")
        self.log("=" * 60, "INFO")

        if not self.test_note_id:
            self.log("No test note ID available", "ERROR")
            self.record_test("Update Note", False, "No note ID")
            return False

        # First get current version
        _, note_data = self.make_request("GET", f"/notes/{self.test_note_id}")
        current_version = note_data.get('version', 1)

        update_data = {
            "title": "Test Note - UPDATED",
            "content": "# Updated API Test Note\n\nThis note was **updated** by the verification script.\n\nUpdate timestamp: " + datetime.now().isoformat(),
            "tags": ["test", "api", "verification", "updated"],
            "version": current_version
        }

        success, data = self.make_request(
            "PUT",
            f"/notes/{self.test_note_id}",
            json=update_data
        )

        if success:
            self.log(f"Note updated to version {data.get('version')}", "SUCCESS")
            self.print_json(data)

        self.record_test("Update Note", success)
        return success

    def test_list_tags(self) -> bool:
        """Test listing all tags."""
        self.log("=" * 60, "INFO")
        self.log("TEST: List Tags", "INFO")
        self.log("=" * 60, "INFO")

        success, data = self.make_request("GET", "/notes/tags")

        if success:
            tags = data.get('tags', [])
            self.log(f"Total unique tags: {len(tags)}", "SUCCESS")
            for tag_info in tags[:5]:  # Show first 5
                self.log(f"  - {tag_info['tag']}: {tag_info['count']} notes", "INFO")
            self.print_json(data)

        self.record_test("List Tags", success)
        return success

    # ===========================
    # SEARCH TESTS
    # ===========================

    def test_semantic_search(self) -> bool:
        """Test semantic search."""
        self.log("=" * 60, "INFO")
        self.log("TEST: Semantic Search", "INFO")
        self.log("=" * 60, "INFO")

        # Wait a moment for indexing
        self.log("Waiting 2 seconds for Weaviate indexing...", "INFO")
        time.sleep(2)

        success, data = self.make_request(
            "GET",
            "/notes/search/semantic",
            params={
                "q": "API test verification",
                "limit": 5
            }
        )

        if success:
            results = data.get('results', [])
            self.log(f"Found {len(results)} results", "SUCCESS")
            for result in results[:3]:
                score = result.get('relevance_score', 0)
                self.log(f"  - {result['title']} (score: {score:.2f})", "INFO")
            self.print_json(data)

        self.record_test("Semantic Search", success)
        return success

    def test_search_within_note(self) -> bool:
        """Test searching within a specific note."""
        self.log("=" * 60, "INFO")
        self.log("TEST: Search Within Note", "INFO")
        self.log("=" * 60, "INFO")

        if not self.test_note_id:
            self.log("No test note ID available", "ERROR")
            self.record_test("Search Within Note", False, "No note ID")
            return False

        success, data = self.make_request(
            "GET",
            f"/notes/{self.test_note_id}/search",
            params={
                "q": "verification script",
                "window": 2
            }
        )

        if success:
            self.log(f"Best match in chunks {data.get('chunk_range')}", "SUCCESS")
            self.log(f"Context preview: {data.get('context', '')[:100]}...", "INFO")
            self.print_json(data)

        self.record_test("Search Within Note", success)
        return success

    def test_reindex_notes(self) -> bool:
        """Test reindexing all notes."""
        self.log("=" * 60, "INFO")
        self.log("TEST: Reindex Notes", "INFO")
        self.log("=" * 60, "INFO")

        success, data = self.make_request("POST", "/notes/reindex")

        if success:
            self.log(f"Total notes: {data.get('total')}", "SUCCESS")
            self.log(f"Successfully indexed: {data.get('success')}", "SUCCESS")
            self.log(f"Errors: {data.get('errors')}", "INFO")
            self.print_json(data)

        self.record_test("Reindex Notes", success)
        return success

    # ===========================
    # CHAT TESTS
    # ===========================

    def test_create_chat_session(self) -> bool:
        """Test creating a chat session."""
        self.log("=" * 60, "INFO")
        self.log("TEST: Create Chat Session", "INFO")
        self.log("=" * 60, "INFO")

        success, data = self.make_request("POST", "/chat/sessions")

        if success:
            self.session_id = data.get('session_id')
            self.log(f"Session created: {self.session_id}", "SUCCESS")
            self.print_json(data)

        self.record_test("Create Chat Session", success)
        return success

    def test_chat_query(self) -> bool:
        """Test chat query with RAG."""
        self.log("=" * 60, "INFO")
        self.log("TEST: Chat Query", "INFO")
        self.log("=" * 60, "INFO")

        if not self.session_id:
            self.log("No session ID available", "WARNING")

        success, data = self.make_request(
            "POST",
            "/chat/query",
            json={
                "message": "What notes do I have about API testing?",
                "session_id": self.session_id,
                "limit": 3
            }
        )

        if success:
            self.log(f"AI Response: {data.get('message')[:200]}...", "SUCCESS")
            context_notes = data.get('context_notes', [])
            self.log(f"Used {len(context_notes)} context notes", "INFO")
            self.print_json(data)

        self.record_test("Chat Query", success)
        return success

    def test_chat_history(self) -> bool:
        """Test retrieving chat history."""
        self.log("=" * 60, "INFO")
        self.log("TEST: Get Chat History", "INFO")
        self.log("=" * 60, "INFO")

        if not self.session_id:
            self.log("No session ID available", "ERROR")
            self.record_test("Chat History", False, "No session ID")
            return False

        success, data = self.make_request(
            "GET",
            "/chat/history",
            params={
                "session_id": self.session_id,
                "limit": 50
            }
        )

        if success:
            messages = data.get('messages', [])
            self.log(f"Retrieved {len(messages)} messages", "SUCCESS")
            self.print_json(data)

        self.record_test("Chat History", success)
        return success

    # ===========================
    # SYNC TESTS
    # ===========================

    def test_sync_notes(self) -> bool:
        """Test note synchronization."""
        self.log("=" * 60, "INFO")
        self.log("TEST: Sync Notes", "INFO")
        self.log("=" * 60, "INFO")

        if not self.device_id:
            self.log("No device ID available", "ERROR")
            self.record_test("Sync Notes", False, "No device ID")
            return False

        sync_data = {
            "device_id": self.device_id,
            "last_sync_timestamp": "2026-01-01T00:00:00Z",
            "notes": []
        }

        success, data = self.make_request(
            "POST",
            "/sync",
            json=sync_data
        )

        if success:
            self.log(f"Notes to update: {len(data.get('notes_to_update', []))}", "SUCCESS")
            self.log(f"Notes to delete: {len(data.get('notes_to_delete', []))}", "SUCCESS")
            self.log(f"Conflicts: {len(data.get('conflicts', []))}", "SUCCESS")
            self.print_json(data)

        self.record_test("Sync Notes", success)
        return success

    # ===========================
    # CLEANUP
    # ===========================

    def test_delete_note(self) -> bool:
        """Test deleting a note."""
        self.log("=" * 60, "INFO")
        self.log("TEST: Delete Note (Cleanup)", "INFO")
        self.log("=" * 60, "INFO")

        if not self.test_note_id:
            self.log("No test note ID available", "WARNING")
            self.record_test("Delete Note", True, "No note to delete")
            return True

        success, data = self.make_request(
            "DELETE",
            f"/notes/{self.test_note_id}"
        )

        if success:
            self.log(f"Note {self.test_note_id} deleted successfully", "SUCCESS")

        self.record_test("Delete Note", success)
        return success

    # ===========================
    # RUN ALL TESTS
    # ===========================

    def run_all_tests(self):
        """Run all API tests in sequence."""
        self.log("=" * 60, "INFO")
        self.log("HEXANOTE API VERIFICATION SCRIPT", "INFO")
        self.log(f"Target: {self.base_url}", "INFO")
        self.log("=" * 60, "INFO")
        print()

        # Run tests in order
        tests = [
            # Authentication
            self.test_health_check,
            self.test_get_token,
            self.test_register_device,

            # Notes CRUD
            self.test_create_note,
            self.test_list_notes,
            self.test_get_note,
            self.test_update_note,
            self.test_list_tags,

            # Search
            self.test_semantic_search,
            self.test_search_within_note,
            self.test_reindex_notes,

            # Chat
            self.test_create_chat_session,
            self.test_chat_query,
            self.test_chat_history,

            # Sync
            self.test_sync_notes,

            # Cleanup
            self.test_delete_note,
        ]

        for test_func in tests:
            try:
                test_func()
                print()  # Blank line between tests
                time.sleep(0.5)  # Brief pause between tests
            except Exception as e:
                self.log(f"Test failed with exception: {str(e)}", "ERROR")
                self.record_test(test_func.__name__, False, str(e))
                print()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test results summary."""
        self.log("=" * 60, "INFO")
        self.log("TEST SUMMARY", "INFO")
        self.log("=" * 60, "INFO")

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['success'])
        failed = total - passed

        self.log(f"Total Tests: {total}", "INFO")
        self.log(f"Passed: {passed}", "SUCCESS")
        self.log(f"Failed: {failed}", "ERROR" if failed > 0 else "INFO")
        print()

        if failed > 0:
            self.log("Failed Tests:", "ERROR")
            for result in self.test_results:
                if not result['success']:
                    details = f" - {result['details']}" if result['details'] else ""
                    self.log(f"  ✗ {result['test']}{details}", "ERROR")

        print()
        if failed == 0:
            self.log("🎉 ALL TESTS PASSED! 🎉", "SUCCESS")
        else:
            self.log(f"⚠️  {failed} test(s) failed", "ERROR")

        return failed == 0


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='HexaNote API Verification Script')
    parser.add_argument('--url', default=BASE_URL, help=f'API base URL (default: {BASE_URL})')
    parser.add_argument('--password', default=PASSWORD, help=f'Authentication password (default: {PASSWORD})')
    parser.add_argument('--test', help='Run specific test (e.g., test_create_note)')

    args = parser.parse_args()

    tester = APITester(args.url, args.password)

    if args.test:
        # Run specific test
        test_method = getattr(tester, args.test, None)
        if test_method and callable(test_method):
            tester.log(f"Running single test: {args.test}", "INFO")
            # Still need to authenticate first
            tester.test_get_token()
            test_method()
            tester.print_summary()
        else:
            print(f"Test '{args.test}' not found")
            sys.exit(1)
    else:
        # Run all tests
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
