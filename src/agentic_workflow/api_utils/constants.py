###
# This file is a mock example just to manage the accessment of each permission
# and user, for time constraint i will keep this way but the most appropriate way
# would have table to store each user with their emails and its roles and other table with the
# i will keep some stuff simpler because of time constraints
###

TOKEN_EXPIRATION_HOURS = 24

users = ["operator-user", "manager-user", "admin-user"]

permissions = {
    "operator-user": "operator",
    "manager-user": "manager",
    "admin-user": "admin",
}

users_passwords = {
    "operator-user": "PgojiNYSCiwQuIVd",
    "manager-user": "nQaV_QCwdPlGe2Ah",
    "admin-user": "wZAw4yHGGkLkECBJ",
}

user_permission = {
    "operator-user": permissions["operator-user"],
    "manager-user": permissions["manager-user"],
    "admin-user": permissions["admin-user"],
}

email_to_user = {
    "operator-user@uorak.com": "operator-user",
    "manager@uorak.com": "manager-user",
    "admin-user@uorak.com": "admin-user",
}
