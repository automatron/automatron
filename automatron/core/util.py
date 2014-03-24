import re


USER_RE = re.compile(r'(.*?)!(.*?)@(.*)')


def parse_user(user):
    m = USER_RE.match(user)
    if not m:
        return user, None, None
    else:
        return m.groups()
