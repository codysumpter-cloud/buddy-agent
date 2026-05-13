from buddy_agent.app_bridge.ibe_more import IBeMoreRequest, acknowledge_request


def test_mobile_bridge_acknowledges_request():
    request = IBeMoreRequest(surface="home", action="show_buddy", buddy_id="buddy-1")
    response = acknowledge_request(request)

    assert response.ok is True
    assert response.buddy_id == "buddy-1"
