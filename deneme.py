from functools import wraps


def check_session_validity():
    print("Valid")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        info = check_session_validity()
        return f(*args, **kwargs)
    return decorated_function


@login_required(3)
def denek(aaaa):
    print(aaaa)

denek(5)


