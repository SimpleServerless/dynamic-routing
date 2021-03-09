from datetime import datetime, date
import json
import re
from aws_lambda_powertools import Logger
from typing import Optional, Any, Dict, Tuple, Callable

log = Logger()

#
# Utility classes
#

class Router:
    def __init__(self):
        self._graphql_endpoint = {}
        self._direct = {}
        self._rest_endpoint = {}

    # Can be used for a simple direct invoke.
    # Example: @router.direct("list_students")
    def direct(self, field_name):

        def decorator(function):
            self._direct[field_name] = {'function': function}
            return function

        return decorator

    # Can be used to resolve ReST calls.
    # Example: @router.route("GET" "/students")
    def rest(self, method, path):

        def decorator(function):
            self._rest_endpoint[f"{method} {path}"] = {'function': function,
                                                       'method': method,
                                                       'path': path}
            return function

        return decorator

    def get_rest_endpoints(self):
        return self._rest_endpoint

    # Can be used to resolve GraphQL Calls
    # Example @router.route("Query", "listStudents")
    def graphql(self, parent, *args):

        field_name = None
        id_field = None
        if len(args) > 0:
            field_name = args[0]
        if len(args) > 1:
            id_field = args[1]

        def decorator(function):
            #   Usage: @router.grqphql("ParentField", "childField", "optionalChildId")
            # Example: @router.grqphql("Query", "myEndpoint")
            #      Or: @router.grqphql("Term", "Students", "termId")
            if field_name is not None:
                self._graphql_endpoint[field_name] = {'function': function,
                                                      'parent': parent,
                                                      'id_field': id_field
                                                      }
            return function

        return decorator

    def get_graphql_endpoints(self):
        return self._graphql_endpoint

    def find_function(self, event: Dict[str, Any]) -> Tuple[Callable, Dict[str, Any]]:

        # Event having route indicates direct invokes or AppSync graphql calls
        if 'route' in event and self._direct.get(event['route']):
            log.info("Resolved direct route " + event['route'])
            return self._direct.get(event['route']), event

        # Event having routeKey indicates API Gateway REST call.
        elif 'routeKey' in event and self._rest_endpoint.get(event['routeKey']):
            log.info("Resolved rest route " + event['routeKey'])
            args: Dict[str, Any] = {}
            if 'body' in event:
                body_str = event['body']
                body_dict = json.loads(body_str)
                args.update(body_dict)
            if 'queryStringParameters' in event:
                args.update(event['queryStringParameters'])
            if 'pathParameters' in event:
                args.update(event['pathParameters'])
            return self._rest_endpoint.get(event['routeKey']), args

        # Event having info.fieldName indicates an AppSync graphql event
        elif 'info' in event and 'fieldName' in event['info']:
            route_name = event['info']['fieldName']
            log.info("Resolved graqphql for fieldName " + route_name)
            args = event['arguments']
            return self._graphql_endpoint.get(route_name), args

        else:
            route_name = f"{event.get('route', '')}{event.get('routeKey', '')}{event.get('info', {}).get('fieldName', '')}"
            raise ValueError(f'"{route_name}" has not been registered as a graphql, rest, or direct endpoint')



class Invocation:
    def __init__(self, router: Router, event: dict):
        self._router = router
        self._event = event

    def call(self):
        function_found, args = self._router.find_function(self._event)
        function = function_found['function']
        function_name = function.__qualname__
        log.debug("start: " + function_name)
        return function(args)



#
# Utility functions
#


def to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def to_camel(name):
    components = name.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + ''.join(x.title() for x in components[1:])


def camelfy(dict_or_list):
    if dict_or_list == None:
        return None
    if isinstance(dict_or_list, dict):
        return camelfy_object(dict_or_list)
    elif isinstance(dict_or_list, list):
        new_list = []
        for item in dict_or_list:
            new_list.append(camelfy_object(item))

        return new_list
    else:
        raise Exception("camelfy could not parse type " + str(type(dict_or_list)))


def camelfy_object(object: dict) -> dict:
    new_object_dict = {}
    for key in object.keys():
        if isinstance(object[key], datetime) or isinstance(object[key], date):
            new_object_dict[to_camel(key)] = str(object[key])
        else:
            new_object_dict[to_camel(key)] = object[key]
    return new_object_dict


