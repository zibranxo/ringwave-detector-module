from ringwave_deepfake.inference.session import CallSession, WindowVerdict

def test_session():
    print("Testing CallSession and Aggregation logic...")
    
    # Test 1: Debounce (needs 2 fakes within 10s)
    session1 = CallSession("call_1")
    
    # Fake 1 (score 0.8)
    session1.record(WindowVerdict(0.0, 4.0, 2, "verified-fake", 0.8))
    assert not session1.alert_fired
    
    # Genuine
    session1.record(WindowVerdict(2.0, 6.0, 1, "clear", 0.1))
    assert not session1.alert_fired
    
    # Fake 2 (score 0.82) - comes within 10s of Fake 1 end
    session1.record(WindowVerdict(4.0, 8.0, 2, "verified-fake", 0.82))
    assert session1.alert_fired, "Alert should have fired due to 2 fakes within 10s"
    assert session1.call_level_verdict() == "fake"
    
    # Test 2: High Confidence Override
    session2 = CallSession("call_2")
    session2.record(WindowVerdict(0.0, 4.0, 2, "verified-fake", 0.95))
    assert session2.alert_fired, "Alert should fire immediately on high confidence"
    
    # Test 3: No alert if fakes are spread out
    session3 = CallSession("call_3")
    session3.record(WindowVerdict(0.0, 4.0, 2, "verified-fake", 0.8))
    assert not session3.alert_fired
    
    # 15 seconds later...
    session3.record(WindowVerdict(15.0, 19.0, 2, "verified-fake", 0.8))
    assert not session3.alert_fired, "Alert should not fire, fakes are spread out > 10s"
    assert session3.call_level_verdict() == "fake" # but call level is still fake
    
    print("CallSession tests passed.\n")

if __name__ == "__main__":
    test_session()
