import resend


def send_newsletter(
    html: str,
    subject: str,
    audience_id: str,
    from_email: str,
    api_key: str,
) -> str:
    """Create and send a broadcast email to the audience via Resend."""
    resend.api_key = api_key

    broadcast = resend.Broadcasts.create({
        "audience_id": audience_id,
        "from": from_email,
        "subject": subject,
        "html": html,
    })

    broadcast_id = broadcast["id"]
    resend.Broadcasts.send(broadcast_id)
    return broadcast_id
