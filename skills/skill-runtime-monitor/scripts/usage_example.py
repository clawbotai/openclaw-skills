#!/usr/bin/env python3
"""
Skill Runtime Monitor — Usage Example
=======================================
Demonstrates the full lifecycle:

1. A "broken skill" is registered with the monitor
2. It fails multiple times with the same error (fingerprint deduplication)
3. It fails with different errors (separate entries)
4. Circuit breaker trips after threshold
5. Reliability report is generated
6. Repair tickets are exported for the Evolutionary Loop

Run from the skill-runtime-monitor/scripts/ directory:
    python usage_example.py
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# Ensure schemas and monitor are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor import SkillMonitor, monitor_skill
from schemas import MonitorConfig


def main():
    """Handle this operation."""
    # Use a temp directory so we don't pollute the real workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Configure with aggressive thresholds for demo purposes
        config = MonitorConfig(
            fail_threshold=3,        # Trip circuit after 3 failures
            window_seconds=600,      # Within 10 minutes
            cooldown_seconds=60,     # 1 minute cooldown
            auto_ticket_threshold=2, # Generate ticket after 2 occurrences
            ledger_path="memory/skill-errors.json",
        )

        monitor = SkillMonitor(config=config, workspace=str(workspace))

        # ------------------------------------------------------------------
        # Define some "skills" — one broken, one flaky, one healthy
        # ------------------------------------------------------------------

        @monitor_skill(monitor)
        def parse_api_response(response: dict) -> str:
            """A skill that parses API responses. Broken: doesn't check for None."""
            # This will throw KeyError when 'data' is missing
            return response["data"]["items"][0]["name"]

        @monitor_skill(monitor, skill_name="fetch-weather")
        def fetch_weather(city: str) -> dict:
            """A flaky skill that sometimes times out."""
            if city == "atlantis":
                raise ConnectionError("DNS resolution failed for weather.api.example.com")
            if city == "":
                raise ValueError("City name cannot be empty")
            return {"city": city, "temp": 72, "unit": "F"}

        @monitor_skill(monitor)
        def calculate_total(items: list) -> float:
            """A healthy skill that works correctly."""
            return sum(item["price"] * item["qty"] for item in items)

        # ------------------------------------------------------------------
        # Simulate usage
        # ------------------------------------------------------------------

        print("=" * 60)
        print("  Skill Runtime Monitor — Demo")
        print("=" * 60)

        # 1. Healthy calls
        print("\n📗 Making successful calls...")
        result = calculate_total([
            {"price": 10.0, "qty": 2},
            {"price": 5.50, "qty": 3},
        ])
        print(f"   calculate_total: ${result}")

        result = fetch_weather("Portland")
        print(f"   fetch_weather: {result}")

        # 2. Deterministic failures (same error, deduplication)
        print("\n📕 Triggering deterministic failures (KeyError)...")
        for i in range(4):
            try:
                parse_api_response({"status": "ok"})  # Missing 'data' key
            except KeyError:
                print(f"   Attempt {i+1}: KeyError caught and logged")
            except RuntimeError as e:
                print(f"   Attempt {i+1}: QUARANTINED — {e}")
                break

        # 3. Different deterministic error on same skill
        #    (skip if already quarantined — circuit breaker blocks all calls)
        print("\n📕 Triggering different error on same skill...")
        try:
            parse_api_response(None)  # TypeError: None is not subscriptable
        except TypeError:
            print("   TypeError caught and logged (separate fingerprint)")
        except RuntimeError:
            print("   Skipped — skill is quarantined (circuit breaker OPEN)")

        # 4. Transient failures
        print("\n📙 Triggering transient failures (network)...")
        for i in range(2):
            try:
                fetch_weather("atlantis")
            except ConnectionError:
                print(f"   Attempt {i+1}: ConnectionError caught (transient)")

        # 5. Deterministic on flaky skill
        print("\n📕 Triggering deterministic failure on fetch-weather...")
        try:
            fetch_weather("")
        except ValueError:
            print("   ValueError caught (deterministic)")

        # ------------------------------------------------------------------
        # Check circuit breaker state
        # ------------------------------------------------------------------
        print("\n\n⚡ Circuit Breaker Status:")
        for skill in ["parse_api_response", "fetch-weather", "calculate_total"]:
            health = monitor.get_skill_health(skill)
            print(f"   {skill}:")
            print(f"     State: {health.circuit.state.value}")
            print(f"     Calls: {health.total_calls} "
                  f"(✅ {health.total_successes} / ❌ {health.total_failures})")
            print(f"     Failure Rate: {health.failure_rate}%")
            print(f"     Quarantined: {health.is_quarantined}")

        # ------------------------------------------------------------------
        # Try calling quarantined skill
        # ------------------------------------------------------------------
        parse_health = monitor.get_skill_health("parse_api_response")
        if parse_health.is_quarantined:
            print("\n\n🚫 Attempting to call quarantined skill...")
            try:
                parse_api_response({"data": {"items": [{"name": "test"}]}})
            except RuntimeError as e:
                print(f"   Blocked! {e}")

        # ------------------------------------------------------------------
        # Generate reliability report
        # ------------------------------------------------------------------
        print("\n\n📊 Reliability Report:")
        print("-" * 60)
        report = monitor.generate_reliability_report()
        print(report.to_summary())

        # ------------------------------------------------------------------
        # Argument correlation
        # ------------------------------------------------------------------
        print("\n\n🔍 Argument Correlation (parse_api_response):")
        correlations = monitor.get_argument_correlation("parse_api_response")
        if correlations:
            for c in correlations:
                print(f"   {c['pattern']} — {c['frequency']}x ({c['pct_of_errors']}% of failures)")
        else:
            print("   No correlations found")

        # ------------------------------------------------------------------
        # Export repair tickets for Evolutionary Loop
        # ------------------------------------------------------------------
        print("\n\n🔧 Repair Tickets for Evolutionary Loop:")
        print("=" * 60)
        tickets = monitor.export_for_evolution()
        for ticket in tickets:
            print(f"\n[{ticket.priority.value.upper()}] {ticket.error_summary}")
            print(f"  Fingerprint: {ticket.ticket_id}")
            print(f"  Occurrences: {ticket.occurrence_count}x")
            print(f"  Fix approach: {ticket.suggested_fix_approach}")

        # Full LLM-readable export
        print("\n\n📋 Full LLM-Readable Export (first ticket):")
        print("-" * 60)
        if tickets:
            print(tickets[0].to_llm_prompt()[:2000])

        # ------------------------------------------------------------------
        # Show the ledger file
        # ------------------------------------------------------------------
        ledger = workspace / "memory" / "skill-errors.json"
        print(f"\n\n💾 Ledger saved to: {ledger}")
        ledger_data = json.loads(ledger.read_text())
        print(f"   Skills tracked: {list(ledger_data.keys())}")
        for skill, data in ledger_data.items():
            print(f"   {skill}: {len(data['errors'])} unique errors, "
                  f"{data['total_failures']} total failures")


if __name__ == "__main__":
    main()
