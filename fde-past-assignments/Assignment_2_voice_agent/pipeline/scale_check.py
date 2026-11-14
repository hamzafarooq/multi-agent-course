"""Estimate voice-agent capacity from DAU and traffic assumptions."""

from __future__ import annotations

import argparse
import json
import math


def estimate_capacity(
    dau: int,
    calls_per_dau: float,
    duration_minutes: float,
    turns_per_minute: float,
    peak_factor: float,
    sessions_per_worker: int,
    headroom: float,
    cost_per_minute: float,
) -> dict:
    daily_calls = dau * calls_per_dau
    daily_minutes = daily_calls * duration_minutes
    average_concurrency = daily_minutes / 1440
    peak_concurrency = average_concurrency * peak_factor
    peak_call_starts_per_second = (daily_calls / 86400) * peak_factor
    provisioned_sessions = peak_concurrency * (1 + headroom)
    workers = math.ceil(provisioned_sessions / sessions_per_worker)
    peak_turns_per_minute = peak_concurrency * turns_per_minute
    return {
        "dailyCalls": round(daily_calls),
        "dailyMinutes": round(daily_minutes),
        "averageConcurrency": round(average_concurrency, 1),
        "peakConcurrency": round(peak_concurrency, 1),
        "peakCallStartsPerSecond": round(peak_call_starts_per_second, 1),
        "provisionedSessions": math.ceil(provisioned_sessions),
        "workers": workers,
        "peakRequestsPerMinutePerStage": round(peak_turns_per_minute),
        "estimatedDailyVariableCost": round(daily_minutes * cost_per_minute, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Aurora voice-agent scale calculator")
    parser.add_argument("--dau", type=int, default=1_000_000)
    parser.add_argument("--calls-per-dau", type=float, default=0.25)
    parser.add_argument("--duration-minutes", type=float, default=4.0)
    parser.add_argument("--turns-per-minute", type=float, default=3.0)
    parser.add_argument("--peak-factor", type=float, default=8.0)
    parser.add_argument("--sessions-per-worker", type=int, default=40)
    parser.add_argument("--headroom", type=float, default=0.30)
    parser.add_argument("--cost-per-minute", type=float, default=0.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = estimate_capacity(
        dau=args.dau,
        calls_per_dau=args.calls_per_dau,
        duration_minutes=args.duration_minutes,
        turns_per_minute=args.turns_per_minute,
        peak_factor=args.peak_factor,
        sessions_per_worker=args.sessions_per_worker,
        headroom=args.headroom,
        cost_per_minute=args.cost_per_minute,
    )
    if args.json:
        print(json.dumps(result, indent=2))
        return

    print("Aurora capacity estimate")
    print(f"  daily calls                 {result['dailyCalls']:>12,}")
    print(f"  daily voice minutes         {result['dailyMinutes']:>12,}")
    print(f"  average concurrent calls    {result['averageConcurrency']:>12,.1f}")
    print(f"  peak concurrent calls       {result['peakConcurrency']:>12,.1f}")
    print(f"  provisioned sessions        {result['provisionedSessions']:>12,}")
    print(f"  workers                     {result['workers']:>12,}")
    print(f"  peak call starts/second     {result['peakCallStartsPerSecond']:>12,.1f}")
    print(f"  requests/minute per stage   {result['peakRequestsPerMinutePerStage']:>12,}")
    print(f"  daily variable cost         ${result['estimatedDailyVariableCost']:>11,.2f}")
    print("\nChange every assumption before treating this as a capacity plan.")


if __name__ == "__main__":
    main()
