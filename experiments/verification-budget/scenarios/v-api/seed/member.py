from api import canonical_email


def member_key(value):
    return "member:" + canonical_email(value)
