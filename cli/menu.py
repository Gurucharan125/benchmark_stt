from __future__ import annotations

from cli import commands


def display_menu():
    """Interactive menu for the AI Receptionist Evaluation Framework."""

    while True:
        print("\n" + "=" * 50)
        print("  AI Receptionist Evaluation Framework")
        print("=" * 50)
        print("  1  Benchmark Direct Providers")
        print("  2  Benchmark Twilio Media Streams")
        print("  3  Benchmark Conversation Relay")
        print("  4  Replay Previous Calls")
        print("  5  Compare Benchmark Runs")
        print("  6  Generate Dashboard")
        print("  7  Export Reports")
        print("  8  Diagnostics")
        print("  9  Settings")
        print("  0  Exit")
        print("-" * 50)

        choice = input("  Select an option: ").strip()

        actions = {
            "1": commands.benchmark_direct,
            "2": commands.benchmark_twilio_media,
            "3": commands.benchmark_conversation_relay,
            "4": commands.replay_calls,
            "5": commands.compare_runs,
            "6": commands.generate_dashboard,
            "7": commands.export_reports,
            "8": commands.diagnostics,
            "9": commands.settings,
        }

        if choice == "0":
            print("\nGoodbye.")
            break
        elif choice in actions:
            try:
                actions[choice]()
            except Exception as e:
                print(f"\nError: {e}")
        else:
            print("\nInvalid choice. Try again.")
