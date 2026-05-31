import json
from http.server import HTTPServer, BaseHTTPRequestHandler

USERS_LIST = [
    {
        "id": 1,
        "username": "theUser",
        "firstName": "John",
        "lastName": "James",
        "email": "john@email.com",
        "password": "12345",
    }
]

RESET_DATA = [
    {
        "id": 1,
        "username": "theUser",
        "firstName": "John",
        "lastName": "James",
        "email": "john@email.com",
        "password": "12345",
    }
]


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def _set_response(self, status_code=200, body=None):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(body if body is not None else {}).encode('utf-8'))

    def _pars_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return None
        try:
            return json.loads(self.rfile.read(content_length).decode('utf-8'))
        except Exception:
            return None

    def _is_valid_user(self, data):
        if not isinstance(data, dict):
            return False
        required = {"id": int, "username": str, "firstName": str, "lastName": str, "email": str, "password": str}
        return all(field in data and isinstance(data[field], required[field]) for field in required)

    def _is_valid_put(self, data):
        if not isinstance(data, dict):
            return False
        required = {"username": str, "firstName": str, "lastName": str, "email": str, "password": str}
        return all(field in data and isinstance(data[field], required[field]) for field in required)

    def do_GET(self):
        global USERS_LIST
        
        if self.path == '/reset':
            USERS_LIST = json.loads(json.dumps(RESET_DATA))
            return self._set_response(200, USERS_LIST)
            
        elif self.path == '/users':
            return self._set_response(200, USERS_LIST)
            
        elif self.path.startswith('/user/'):
            username = self.path[6:]
            if username and '/' not in username:
                user = next((u for u in USERS_LIST if u['username'] == username), None)
                if user:
                    return self._set_response(200, user)
                else:
                    return self._set_response(400, {"error": "User not found"})
                    
        return self._set_response(404, {"error": "Not Found"})

    def do_POST(self):
        global USERS_LIST
        body = self._pars_body()
        
        is_valid = False
        is_list = False
        
        if isinstance(body, dict):
            if self._is_valid_user(body):
                is_valid = True
        elif isinstance(body, list):
            if len(body) > 0 and all(self._is_valid_user(u) for u in body):
                is_valid = True
                is_list = True
                
        if not is_valid:
            return self._set_response(400, {})

        if self.path == '/user':
            if is_list or any(u['id'] == body['id'] for u in USERS_LIST):
                return self._set_response(400, {})
            USERS_LIST.append(body)
            return self._set_response(201, body)

        elif self.path == '/user/createWithList':
            if not is_list:
                return self._set_response(400, {})
            input_ids = [u['id'] for u in body]
            existing_ids = [u['id'] for u in USERS_LIST]
            if any(id_ in existing_ids for id_ in input_ids) or len(input_ids) != len(set(input_ids)):
                return self._set_response(400, {})
            USERS_LIST.extend(body)
            return self._set_response(201, body)

        return self._set_response(404, {})

    def do_PUT(self):
        global USERS_LIST
        
        if self.path.startswith('/user/'):
            id_str = self.path[6:]
            try:
                user_id = int(id_str)
            except ValueError:
                return self._set_response(404, {"error": "User not found"})
                
            body = self._pars_body()
            if not self._is_valid_put(body):
                return self._set_response(400, {"error": "not valid request data"})
                
            user = next((u for u in USERS_LIST if u['id'] == user_id), None)
            if not user:
                return self._set_response(404, {"error": "User not found"})
                
            user.update({
                "username": body["username"],
                "firstName": body["firstName"],
                "lastName": body["lastName"],
                "email": body["email"],
                "password": body["password"]
            })
            return self._set_response(200, user)
            
        return self._set_response(404, {})

    def do_DELETE(self):
        global USERS_LIST
        
        if self.path.startswith('/user/'):
            id_str = self.path[6:]
            try:
                user_id = int(id_str)
            except ValueError:
                return self._set_response(404, {"error": "User not found"})
                
            user_index = next((i for i, u in enumerate(USERS_LIST) if u['id'] == user_id), None)
            if user_index is not None:
                USERS_LIST.pop(user_index)
                return self._set_response(200, {})
            else:
                return self._set_response(404, {"error": "User not found"})
                
        return self._set_response(404, {"error": "User not found"})


def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, host='localhost', port=8000):
    server_address = (host, port)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()