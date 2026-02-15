"""
LABBAIK AI v6.0 - Page Tracking Integration Guide
=================================================

Add this ONE LINE at the top of each page's main render function:

    from services.analytics import track_page
    track_page("page_name")

Example for each page:
----------------------

# ui/pages/chat.py
def render_chat_page():
    from services.analytics import track_page
    track_page("chat")
    # ... rest of the page code

# ui/pages/simulator.py  
def render_simulator_page():
    from services.analytics import track_page
    track_page("simulator")
    # ... rest of the page code

# ui/pages/umrah_mandiri.py
def render_umrah_mandiri_page():
    from services.analytics import track_page
    track_page("umrah_mandiri")
    # ... rest of the page code

# ui/pages/umrah_bareng.py
def render_umrah_bareng_page():
    from services.analytics import track_page
    track_page("umrah_bareng")
    # ... rest of the page code

# ui/pages/booking.py
def render_booking_page():
    from services.analytics import track_page
    track_page("booking")
    # ... rest of the page code

That's it! The analytics service handles:
- Session management
- Unique visitor detection
- Page view counting
- Daily aggregation
- Engagement metrics

"""

# Quick integration script - run this to add tracking to all pages
PAGES_TO_TRACK = [
    ("ui/pages/chat.py", "chat"),
    ("ui/pages/simulator.py", "simulator"),
    ("ui/pages/umrah_mandiri.py", "umrah_mandiri"),
    ("ui/pages/umrah_bareng.py", "umrah_bareng"),
    ("ui/pages/booking.py", "booking"),
]

TRACKING_CODE = '''
    # Track page view
    try:
        from services.analytics import track_page
        track_page("{page_name}")
    except Exception:
        pass
'''

def add_tracking_to_page(filepath: str, page_name: str):
    """Add tracking code to a page file."""
    import re
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if already has tracking
    if 'track_page' in content:
        print(f"✓ {filepath} already has tracking")
        return False
    
    # Find the main render function and add tracking after def line
    pattern = r'(def render_\w+_page\(\):\s*(?:"""[^"]*""")?\s*)'
    replacement = r'\1' + TRACKING_CODE.format(page_name=page_name)
    
    new_content = re.sub(pattern, replacement, content, count=1)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"✓ Added tracking to {filepath}")
        return True
    else:
        print(f"✗ Could not find render function in {filepath}")
        return False

if __name__ == "__main__":
    print("Adding analytics tracking to pages...")
    for filepath, page_name in PAGES_TO_TRACK:
        try:
            add_tracking_to_page(filepath, page_name)
        except Exception as e:
            print(f"✗ Error with {filepath}: {e}")
