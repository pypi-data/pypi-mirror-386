"""
Balance Management Example

Example showing how to check balance and usage history.
"""

import orbitalsai
from datetime import date, timedelta

def main():
    # Initialize the client
    client = orbitalsai.Client(api_key="your_api_key_here")
    
    # Check current balance
    balance = client.get_balance()
    print(f"Current balance: ${balance.balance:.2f}")
    print(f"Last updated: {balance.last_updated}")
    
    # Get daily usage for the last 7 days
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    print(f"\nUsage for {start_date} to {end_date}:")
    daily_usage = client.get_daily_usage(start_date=start_date, end_date=end_date)
    
    print(f"Total cost: ${daily_usage.total_cost:.2f}")
    print(f"Total audio processed: {daily_usage.total_audio_seconds:.1f} seconds")
    
    print("\nDaily breakdown:")
    for record in daily_usage.daily_records:
        print(f"  {record.date}: ${record.total_cost:.4f} ({record.transcription_usage:.1f}s transcription)")
        if record.translation_usage > 0:
            print(f"    - Translation: ${record.translation_cost:.4f} ({record.translation_usage:.1f}s)")
        if record.summarization_usage > 0:
            print(f"    - Summarization: ${record.summarization_cost:.4f} ({record.summarization_usage:.1f}s)")
    
    # Get detailed usage history
    print(f"\nDetailed usage history:")
    usage_history = client.get_usage_history(page_size=10)
    
    for record in usage_history.records:
        print(f"  {record.timestamp.strftime('%Y-%m-%d %H:%M')}: "
              f"{record.service_type} - ${record.cost:.2f} ({record.usage_amount:.1f}s)")

if __name__ == "__main__":
    main()
