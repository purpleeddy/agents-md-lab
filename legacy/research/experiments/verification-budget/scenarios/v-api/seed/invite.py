from api import canonical_email


def invite_key(value):
    return "invite:" + canonical_email(value)
