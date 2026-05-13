from buddy_agent.gateway import Contact, InboundMessage, OutboundMessage


def test_gateway_contracts_store_normalized_values():
    contact = Contact(platform="cli", user_id="local", display_name="Local User")
    inbound = InboundMessage(contact=contact, text="hello", channel_id="dev")
    outbound = OutboundMessage(text="hi", channel_id=inbound.channel_id)

    assert inbound.contact.platform == "cli"
    assert inbound.text == "hello"
    assert outbound.text == "hi"
    assert outbound.channel_id == "dev"
