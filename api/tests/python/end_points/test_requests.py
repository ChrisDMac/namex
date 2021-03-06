from flask import jsonify
from flask import json
from namex.models import User

token_header = {
                "alg": "RS256",
                "typ": "JWT",
                "kid": "flask-jwt-oidc-test-client"
               }
claims = {
            "iss": "https://sso-dev.pathfinder.gov.bc.ca/auth/realms/sbc",
            "sub": "43e6a245-0bf7-4ccf-9bd0-e7fb85fd18cc",
            "aud": "NameX-Dev",
            "exp": 31531718745,
            "iat": 1531718745,
            "jti": "flask-jwt-oidc-test-support",
            "typ": "Bearer",
            "username": "test-user",
            "realm_access": {
                "roles": [
                    "{}".format(User.EDITOR),
                    "{}".format(User.APPROVER),
                    "viewer",
                    "user"
                ]
            }
         }

claims_editor = {
            "iss": "https://sso-dev.pathfinder.gov.bc.ca/auth/realms/sbc",
            "sub": "43e6a245-0bf7-4ccf-9bd0-e7fb85fd18cc",
            "aud": "NameX-Dev",
            "exp": 21531718745,
            "iat": 1531718745,
            "jti": "flask-jwt-oidc-test-support",
            "typ": "Bearer",
            "username": "test-user",
            "realm_access": {
                "roles": [
                    "{}".format(User.VIEWONLY),
                    "{}".format(User.EDITOR),
                    "user"
                ]
            }
         }

claims_viewer = {
            "iss": "https://sso-dev.pathfinder.gov.bc.ca/auth/realms/sbc",
            "sub": "43e6a245-0bf7-4ccf-9bd0-e7fb85fd18cc",
            "aud": "NameX-Dev",
            "exp": 11531718745,
            "iat": 1531718745,
            "jti": "flask-jwt-oidc-test-support",
            "typ": "Bearer",
            "username": "test-user",
            "realm_access": {
                "roles": [
                    "{}".format(User.VIEWONLY),
                    "user"
                ]
            }
         }


def test_get_next(client, jwt, app):

    # add NR to database
    from namex.models import Request as RequestDAO, State
    nr = RequestDAO()
    nr.nrNum='NR 0000001'
    nr.stateCd = State.DRAFT
    nr.save_to_db()

    # create JWT & setup header with a Bearer Token using the JWT
    token = jwt.create_jwt(claims, token_header)
    headers = {'Authorization': 'Bearer ' + token}

    # The message expected to be returned
    json_msg = jsonify(nameRequest='NR 0000001')

    # get the resource (this is the test)
    rv = client.get('/api/v1/requests/queues/@me/oldest', headers=headers)

    assert b'"nameRequest": "NR 0000001"' in rv.data


def test_get_next_no_draft_avail(client, jwt, app):

    # add NR to database
    from namex.models import Request as RequestDAO, State
    nr = RequestDAO()
    nr.nrNum='NR 0000001'
    nr.stateCd = State.APPROVED
    nr.save_to_db()

    # create JWT & setup header with a Bearer Token using the JWT
    token = jwt.create_jwt(claims, token_header)
    headers = {'Authorization': 'Bearer ' + token}

    # get the resource (this is the test)
    rv = client.get('/api/v1/requests/queues/@me/oldest', headers=headers)

    # should return 404, not found
    assert 404 == rv.status_code


def test_get_next_oldest(client, jwt, app):

    # add NR to database
    from namex.models import Request as RequestDAO, State
    nr = RequestDAO()
    nr.nrNum='NR 0000001'
    nr.stateCd = State.DRAFT
    nr.save_to_db()

    for i in range(2,12):
        nr = RequestDAO()
        nr.nrNum = 'NR {0:07d}'.format(i)
        nr.stateCd = State.DRAFT
        nr.save_to_db()

    # create JWT & setup header with a Bearer Token using the JWT
    token = jwt.create_jwt(claims, token_header)
    headers = {'Authorization': 'Bearer ' + token}

    # The message expected to be returned
    json_msg = jsonify(nameRequest='NR 0000001')

    # get the resource (this is the test)
    rv = client.get('/api/v1/requests/queues/@me/oldest', headers=headers)

    assert b'"nameRequest": "NR 0000001"' in rv.data


def test_get_next_not_approver(client, jwt, app):

    # add NR to database
    from namex.models import Request as RequestDAO, State
    nr = RequestDAO()
    nr.nrNum='NR 0000001'
    nr.stateCd = State.DRAFT
    nr.save_to_db()

    # create JWT & setup header with a Bearer Token using the JWT
    token = jwt.create_jwt(claims_editor, token_header)
    headers = {'Authorization': 'Bearer ' + token}

    expected_response = b'{\n  "code": "missing_required_roles", \n  "description": "Missing the role(s) required to access this endpoint"\n}\n'
    # get the resource (this is the test)
    rv = client.get('/api/v1/requests/queues/@me/oldest', headers=headers)

    assert rv.data == expected_response


def test_get_nr_view_only(client, jwt, app):

    # add NR to database
    from namex.models import Request as RequestDAO, State
    nr = RequestDAO()
    nr.nrNum='NR 0000001'
    nr.stateCd = State.DRAFT
    nr.save_to_db()
    print("Role: {} ".format(claims_viewer.get('realm_access').get('roles')))

    # create JWT & setup header with a Bearer Token using the JWT
    token = jwt.create_jwt(claims_viewer, token_header)
    headers = {'Authorization': 'Bearer ' + token}

    # The message expected to be returned
    json_msg = jsonify(nameRequest='NR 0000001')

    # get the resource (this is the test)
    rv = client.get('/api/v1/requests/NR%200000001', headers=headers)

    assert 200 == rv.status_code


def test_patch_nr_view_only(client, jwt, app):

    # create JWT & setup header with a Bearer Token using the JWT
    token = jwt.create_jwt(claims_viewer, token_header)
    headers = {'Authorization': 'Bearer ' + token}

    expected_response = b'{\n  "code": "missing_a_valid_role", \n  "description": "Missing a role required to access this endpoint"\n}\n'

    # The message expected to be returned
    json_msg = jsonify(nameRequest='NR 0000001')

    # try to patch for a view only user.  NR doesn't exist in db but we don't care.
    rv = client.patch('/api/v1/requests/NR%200000001', headers=headers)

    assert 401 == rv.status_code
    assert expected_response == rv.data


def test_put_nr_view_only(client, jwt, app):

    # create JWT & setup header with a Bearer Token using the JWT
    token = jwt.create_jwt(claims_viewer, token_header)
    headers = {'Authorization': 'Bearer ' + token}

    expected_response = b'{\n  "code": "missing_a_valid_role", \n  "description": "Missing a role required to access this endpoint"\n}\n'

    # The message expected to be returned
    json_msg = jsonify(nameRequest='NR 0000001')

    # try to patch for a view only user.  NR doesn't exist in db but we don't care.
    rv = client.put('/api/v1/requests/NR%200000001', headers=headers)

    assert 401 == rv.status_code
    assert expected_response == rv.data


def test_add_new_name_to_nr(client, jwt, app):

    # add NR to database
    from namex.models import Request as RequestDAO, State, Name as NameDAO
    nr = RequestDAO()
    nr.nrNum = 'NR 0000002'
    nr.stateCd = State.INPROGRESS
    nr.requestId = 1460775
    name1 = NameDAO()
    name1.choice = 1
    name1.name = 'ONE'
    nr.names = [name1]
    nr.save_to_db()

    # create JWT & setup header with a Bearer Token using the JWT
    token = jwt.create_jwt(claims, token_header)
    headers = {'Authorization': 'Bearer ' + token, 'content-type': 'application/json'}

    # get the resource so we have a template for the request:
    rv = client.get('/api/v1/requests/NR%200000002', headers=headers)
    assert rv.status_code == 200
    # assert we're starting with just one name:
    data = json.loads(rv.data)
    assert len(data['names']) == 1

    new_name = data['names'][0]
    new_name['name'] = 'Name 2'
    new_name['choice'] = 2
    data['names'].append(new_name)

    # Update with a brand new name (this is the test)
    rv = client.put('/api/v1/requests/NR%200000002', data=json.dumps(data), headers=headers)

    data = json.loads(rv.data)
    assert 200 == rv.status_code
    assert len(data['names']) == 2


def test_remove_name_from_nr(client, jwt, app):

    # add NR to database
    from namex.models import Request as RequestDAO, State, Name as NameDAO
    nr = RequestDAO()
    nr.nrNum = 'NR 0000002'
    nr.stateCd = State.INPROGRESS
    nr.requestId = 1460775
    name1 = NameDAO()
    name1.choice = 1
    name1.name = 'ONE'
    name2 = NameDAO()
    name2.choice = 2
    name2.name = 'TWO'
    nr.names = [name1, name2]
    nr.save_to_db()

    # create JWT & setup header with a Bearer Token using the JWT
    token = jwt.create_jwt(claims, token_header)
    headers = {'Authorization': 'Bearer ' + token, 'content-type': 'application/json'}

    # get the resource so we have a template for the request:
    rv = client.get('/api/v1/requests/NR%200000002', headers=headers)
    assert rv.status_code == 200
    # assert we're starting with just one name:
    data = json.loads(rv.data)
    assert len(data['names']) == 2

    for name in data['names'] :
        if name['choice'] == 2:
            name['name'] = ''

    # Update with one blank name name (should remove the blank name)
    rv = client.put('/api/v1/requests/NR%200000002', data=json.dumps(data), headers=headers)

    data = json.loads(rv.data)
    assert 200 == rv.status_code
    assert len(data['names']) == 1