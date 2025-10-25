import typing

import lms.model.backend
import lms.model.assignments
import lms.model.courses
import lms.model.users
import lms.util.parse

def check_required_course(
        backend: lms.model.backend.APIBackend,
        config: typing.Dict[str, typing.Any],
        ) -> typing.Union[lms.model.courses.CourseQuery, None]:
    """
    Fetch and ensure that a course is provided in the config.
    If no course is provided, print a message and return None.
    """

    course = lms.util.parse.optional_string(config.get('course', None))
    if (course is None):
        print('ERROR: No course has been provided.')
        return None

    query = backend.parse_course_query(course)
    if (query is None):
        print('ERROR: Course query is malformed.')
        return None

    return query

def check_required_assignment(
        backend: lms.model.backend.APIBackend,
        config: typing.Dict[str, typing.Any],
        ) -> typing.Union[lms.model.assignments.AssignmentQuery, None]:
    """
    Fetch and ensure that an assignment is provided in the config.
    If no assignment is provided, print a message and return None.
    """

    assignment = lms.util.parse.optional_string(config.get('assignment', None))
    if (assignment is None):
        print('ERROR: No assignment has been provided.')
        return None

    query = backend.parse_assignment_query(assignment)
    if (query is None):
        print('ERROR: Assignment query is malformed.')
        return None

    return query

def check_required_user(
        backend: lms.model.backend.APIBackend,
        config: typing.Dict[str, typing.Any],
        ) -> typing.Union[lms.model.users.UserQuery, None]:
    """
    Fetch and ensure that a user is provided in the config.
    If no user is provided, print a message and return None.
    """

    user = lms.util.parse.optional_string(config.get('user', None))
    if (user is None):
        print('ERROR: No user has been provided.')
        return None

    query = backend.parse_user_query(user)
    if (query is None):
        print('ERROR: User query is malformed.')
        return None

    return query
