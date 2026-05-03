from data import fetch_events


def test_events_query_returns_list():
    events = fetch_events(
        ["guest lecture", "career", "workshop", "showcase"]
    )
    assert isinstance(events, list), "fetch_events must return a list"


def test_events_have_required_fields():
    events = fetch_events(
        ["guest lecture", "career", "workshop", "showcase"]
    )
    for e in events:
        assert "title" in e and e["title"], "event missing title"
        assert "event_date" in e and e["event_date"], "event missing event_date"
        assert "category" in e and e["category"], "event missing category"
