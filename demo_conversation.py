"""
Demo: eCourts Chatbot Conversation Flow
Shows exactly how the chatbot will interact with you
"""
import time
import sys

def print_bot(message, delay=0.5):
    """Print bot message"""
    print(f"\n🤖 Bot: {message}")
    time.sleep(delay)

def print_user(message, delay=0.3):
    """Print user message"""
    print(f"👤 You: {message}")
    time.sleep(delay)

def print_captcha():
    """Simulate CAPTCHA display"""
    print("\n" + "="*60)
    print("📸 CAPTCHA IMAGE CAPTURED FROM eCOURTS:")
    print("="*60)
    print("""
    ┌─────────────────────────────┐
    │                             │
    │      A  B  C  1  2  3       │  ← CAPTCHA image from eCourts
    │                             │
    └─────────────────────────────┘
    """)
    print("Please enter the text you see above:")
    print("="*60)

def print_results():
    """Simulate result display"""
    print("\n" + "="*60)
    print("✅ CASE DETAILS RETRIEVED FROM eCOURTS")
    print("="*60)
    print("""
┌─────────────────────────────────────────────────────────┐
│ CNR: DLND010019612022                                   │
├─────────────────────────────────────────────────────────┤
│ Case Number: CS(OS) 123/2022                            │
│ Filing Number: 12345/2022                               │
│ Filing Date: 15-03-2022                                 │
│                                                         │
│ Court: District Court, New Delhi                        │
│ Judge: Hon'ble Justice XYZ                              │
│                                                         │
│ Petitioner: ABC Company Ltd.                            │
│ Respondent: XYZ Enterprises                             │
│                                                         │
│ Case Type: Civil Suit                                   │
│ Status: Pending                                         │
│ Next Hearing: 15-01-2025                                │
│                                                         │
│ Acts: Contract Act, 1872 - Section 73                   │
│       Indian Evidence Act, 1872                         │
└─────────────────────────────────────────────────────────┘
    """)

def main():
    print("\n" + "="*60)
    print("  🏛️  eCOURTS CHATBOT - CONVERSATION DEMO")
    print("="*60)
    print("\nShowing exactly how the chatbot will work for you...")
    time.sleep(2)

    # Welcome
    print_bot("Hello! I'm your eCourts assistant. I can help you search for case details.")
    print_bot("How would you like to search?")
    print("     [Search by CNR]  [Search by Party Name]")

    time.sleep(1)
    print_user("Search by CNR")

    # CNR input
    print_bot("Great! Please enter the CNR number (16-digit Case Number).")
    print_bot("Example: MHMM01-0123-456789-2023")

    time.sleep(1)
    print_user("DLND010019612022")

    # Processing
    print_bot("Got it! I'll search for CNR: DLND010019612022")
    print_bot("Please wait while I access the eCourts system...")

    print("\n⏳ [Backend is now:]")
    print("   1. Opening eCourts website...")
    print("   2. Clicking on 'CNR Number' tab...")
    print("   3. Filling CNR: DLND010019612022...")
    print("   4. Capturing CAPTCHA image...")
    time.sleep(2)

    # CAPTCHA
    print_bot("I've filled the form. Now I need you to solve the CAPTCHA:")
    print_captcha()

    time.sleep(1)
    print_user("ABC123")

    # Submit
    print_bot("Submitting CAPTCHA and fetching results...")

    print("\n⏳ [Backend is now:]")
    print("   1. Entering CAPTCHA: ABC123...")
    print("   2. Clicking Submit button...")
    print("   3. Waiting for results page...")
    print("   4. Scraping case details...")
    print("   5. Formatting results...")
    time.sleep(2)

    # Results
    print_bot("✅ Search completed! Here are the case details:")
    print_results()

    # Follow up
    print_bot("Would you like to search for another case?")
    print("     [Yes, search again]  [No, thank you]")

    print("\n" + "="*60)
    print("  DEMO COMPLETE")
    print("="*60)
    print("\n📊 What just happened:")
    print("  ✓ Chatbot asked for search type")
    print("  ✓ You provided CNR number")
    print("  ✓ Backend automated eCourts form filling")
    print("  ✓ CAPTCHA was captured and shown to you")
    print("  ✓ You solved the CAPTCHA (human verification)")
    print("  ✓ Backend submitted and scraped results")
    print("  ✓ Results displayed in clean format")
    print("\n🎯 This is EXACTLY how it will work when you run it!")
    print("\n📝 Your actual search will return REAL data from eCourts")
    print("   for CNR: DLND010019612022")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
        sys.exit(0)
