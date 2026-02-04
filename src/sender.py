import resend


def send_newsletter(
    html: str,
    subject: str,
    audience_id: str,
    from_email: str,
    api_key: str,
) -> list[str]:
    """Send newsletter to all contacts in an audience via direct email."""
    resend.api_key = api_key

    # Get all contacts from the audience
    contacts = resend.Contacts.list(audience_id=audience_id)

    # Filter to only subscribed contacts
    recipients = [
        c["email"] for c in contacts["data"]
        if not c.get("unsubscribed", False)
    ]

    if not recipients:
        print("No subscribed contacts in audience. Skipping send.")
        return []

    # Send to each recipient
    email_ids = []
    for recipient in recipients:
        result = resend.Emails.send({
            "from": from_email,
            "to": [recipient],
            "subject": subject,
            "html": html,
        })
        email_ids.append(result["id"])
        print(f"Sent to {recipient}: {result['id']}")

    return email_ids
