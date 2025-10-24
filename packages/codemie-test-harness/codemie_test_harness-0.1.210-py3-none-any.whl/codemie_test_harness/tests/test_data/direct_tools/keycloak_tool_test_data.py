KEYCLOAK_DIRECT_TOOL_PROMPT = {
    "method": "GET",
    "relative_url": "/users/profile",
    "params": "",
}

KEYCLOAK_DIRECT_TOOL_RESPONSE = """
    {
    "attributes": [
        {
            "name": "username",
            "displayName": "${username}",
            "validations": {
                "length": {
                    "min": 3,
                    "max": 255
                },
                "username-prohibited-characters": {},
                "up-username-not-idn-homograph": {}
            },
            "permissions": {
                "view": [
                    "admin",
                    "user"
                ],
                "edit": [
                    "admin",
                    "user"
                ]
            },
            "multivalued": false
        },
        {
            "name": "email",
            "displayName": "${email}",
            "validations": {
                "email": {},
                "length": {
                    "max": 255
                }
            },
            "required": {
                "roles": [
                    "user"
                ]
            },
            "permissions": {
                "view": [
                    "admin",
                    "user"
                ],
                "edit": [
                    "admin",
                    "user"
                ]
            },
            "multivalued": false
        },
        {
            "name": "firstName",
            "displayName": "${firstName}",
            "validations": {
                "length": {
                    "max": 255
                },
                "person-name-prohibited-characters": {}
            },
            "required": {
                "roles": [
                    "user"
                ]
            },
            "permissions": {
                "view": [
                    "admin",
                    "user"
                ],
                "edit": [
                    "admin",
                    "user"
                ]
            },
            "multivalued": false
        },
        {
            "name": "lastName",
            "displayName": "${lastName}",
            "validations": {
                "length": {
                    "max": 255
                },
                "person-name-prohibited-characters": {}
            },
            "required": {
                "roles": [
                    "user"
                ]
            },
            "permissions": {
                "view": [
                    "admin",
                    "user"
                ],
                "edit": [
                    "admin",
                    "user"
                ]
            },
            "multivalued": false
        }
    ],
    "groups": [
        {
            "name": "user-metadata",
            "displayHeader": "User metadata",
            "displayDescription": "Attributes, which refer to user metadata"
        }
    ]
}
"""
