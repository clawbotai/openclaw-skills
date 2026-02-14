import unittest
import tempfile
import shutil
import json
import time
import os
import sys
from pathlib import Path

# Add scripts directory to path to allow importing monitor
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_SCRIPTS_DIR = SCRIPT_DIR.parent / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS_DIR))

try:
    import monitor
except ImportError:
    # Fallback if running from root
    sys.path.append("skills/forge/scripts")
    import monitor

class TestMonitor(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for memory to avoid polluting real logs
        self.test_dir = tempfile.mkdtemp()
        self.memory_dir = Path(self.test_dir) / "memory"
        self.memory_dir.mkdir(parents=True)
        
        # Define test log paths
        self.error_log = self.memory_dir / "forge-errors.json"
        self.ticket_log = self.memory_dir / "repair-tickets.md"
        
        # Initialize monitor and override paths
        self.monitor = monitor.SkillMonitor(Path(self.test_dir))
        self.monitor.error_log_path = self.error_log
        self.monitor.ticket_log_path = self.ticket_log

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_classify_error(self):
        """Test error classification logic."""
        # Transient errors
        self.assertEqual(self.monitor.classify_error(Exception("Connection timed out")), "transient")
        self.assertEqual(self.monitor.classify_error(Exception("503 Service Unavailable")), "transient")
        self.assertEqual(self.monitor.classify_error(Exception("Rate limit exceeded")), "transient")
        self.assertEqual(self.monitor.classify_error(Exception("Temporary failure")), "transient")
        
        # Deterministic errors
        self.assertEqual(self.monitor.classify_error(ValueError("Invalid argument")), "deterministic")
        self.assertEqual(self.monitor.classify_error(KeyError("Missing key")), "deterministic")
        self.assertEqual(self.monitor.classify_error(Exception("Syntax error")), "deterministic")
        # Unknown errors default to deterministic
        self.assertEqual(self.monitor.classify_error(Exception("Something weird happened")), "deterministic")

    def test_check_circuit_breaker_clean(self):
        """Test circuit breaker is closed (None) when no errors exist."""
        self.assertIsNone(self.monitor.check_circuit_breaker())

    def test_check_circuit_breaker_tripped(self):
        """Test circuit breaker trips after threshold failures in window."""
        # Create 5 errors within the window (e.g., last 10 seconds)
        errors = []
        now = time.time()
        for _ in range(5):
            errors.append({
                "timestamp": now - 10,
                "error_type": "ValueError",
                "classification": "deterministic"
            })
        
        # Write to log manually to simulate state
        self.error_log.write_text(json.dumps(errors))
        
        status = self.monitor.check_circuit_breaker()
        self.assertIsNotNone(status)
        self.assertIn("Circuit breaker OPEN", status)

    def test_check_circuit_breaker_ignores_old_errors(self):
        """Test circuit breaker ignores errors outside the window."""
        # Create 5 errors older than WINDOW_SECONDS (300s)
        errors = []
        now = time.time()
        for _ in range(5):
            errors.append({
                "timestamp": now - 350, 
                "error_type": "ValueError",
                "classification": "deterministic"
            })
            
        self.error_log.write_text(json.dumps(errors))
        
        self.assertIsNone(self.monitor.check_circuit_breaker())

    def test_log_failure_creates_ticket_for_deterministic(self):
        """Test that logging a deterministic failure creates a repair ticket."""
        error = ValueError("Invalid configuration")
        self.monitor.log_failure("test_mode", ["arg1"], error, 1.5)
        
        # Check error log updated
        errors = json.loads(self.error_log.read_text())
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error_type"], "ValueError")
        self.assertEqual(errors[0]["classification"], "deterministic")
        
        # Check ticket created
        self.assertTrue(self.ticket_log.exists())
        content = self.ticket_log.read_text()
        self.assertIn("ValueError", content)
        self.assertIn("Invalid configuration", content)
        self.assertIn("Priority: HIGH", content)

    def test_log_failure_no_ticket_for_transient(self):
        """Test that logging a single transient failure does NOT create a ticket."""
        error = Exception("Connection timeout")
        self.monitor.log_failure("test_mode", ["arg1"], error, 1.5)
        
        # Check error log updated
        errors = json.loads(self.error_log.read_text())
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["classification"], "transient")
        
        # Check NO ticket created
        self.assertFalse(self.ticket_log.exists())

    def test_log_failure_ticket_on_circuit_break(self):
        """Test that logging a transient failure creates a ticket if circuit breaks."""
        # Pre-fill 4 errors
        errors = []
        now = time.time()
        for _ in range(4):
            errors.append({
                "timestamp": now - 10,
                "error_type": "TimeoutError",
                "classification": "transient"
            })
        self.error_log.write_text(json.dumps(errors))

        # Log the 5th error
        error = Exception("TimeoutError")
        self.monitor.log_failure("test_mode", ["arg1"], error, 1.5)
        
        # Check ticket created with CRITICAL priority
        self.assertTrue(self.ticket_log.exists())
        content = self.ticket_log.read_text()
        self.assertIn("Priority: CRITICAL", content)
        self.assertIn("Circuit breaker OPEN", self.monitor.check_circuit_breaker())

if __name__ == '__main__':
    unittest.main()
