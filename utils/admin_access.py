ADMIN_NUMBERS = ['918074301029', '916281880981']

def check_admin_access(sender):
    if sender in ADMIN_NUMBERS:
        return True, None
    else:
        message = "Hi there! This information is currently reserved for our admin team. We're happy to assist you with anything else you need!"
        return False, message