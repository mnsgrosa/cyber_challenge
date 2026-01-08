###
# This file is a mock example just to manage the accessment of each permission
# and user, for time constraint i will keep this way but the most appropriate way
# would have table to store each user with their emails and its roles and other table with the
# i will keep some stuff simpler because of time constraints
###

TOKEN_EXPIRATION_HOURS = 24

users = ["operator-user", "manager=user", "admin-user"]

permissions = {
    "operator": {
        "dashboard": True,
        "management_page": False,
        "crud": False,
        "delete": False,
    },
    "manager": {
        "dashboard": True,
        "management_page": False,
        "crud": True,
        "delete": False,
    },
    "admin": {"dashboard": True, "management_page": True, "crud": True, "delete": True},
}

users_passwords = {
    "operator-user": "PgojiNYSCiwQuIVd",
    "manager-user": "nQaV_QCwdPlGe2Ah",
    "admin-user": "wZAw4yHGGkLkECBJ",
}

user_permission = {
    "operator-user": permissions["operator"],
    "manager-user": permissions["manager"],
    "admin-user": permissions["admin"],
}

email_to_user = {
    "operator-user@uorak.com": "operator-user",
    "manager@uorak.com": "manager-user",
    "admin-user@uorak.com": "admin-user",
}
