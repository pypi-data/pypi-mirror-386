import typing

import lms.backend.canvas.common
import lms.backend.canvas.model.users

BASE_ENDPOINT = "/api/v1/courses/{course_id}/users?per_page={page_size}"

def request(backend: typing.Any,
        course_id: int,
        include_role: bool = True,
        ) -> typing.List[lms.backend.canvas.model.users.CourseUser]:
    """ List course users. """

    url = backend.server + BASE_ENDPOINT.format(course_id = course_id, page_size = lms.backend.canvas.common.DEFAULT_PAGE_SIZE)
    headers = backend.get_standard_headers()

    if (include_role):
        url += '&include[]=enrollments'

    raw_objects = lms.backend.canvas.common.make_get_request_list(url, headers)
    if (raw_objects is None):
        identifiers = {
            'course_id': course_id,
        }
        backend.not_found('course', identifiers)

        return []

    return [lms.backend.canvas.model.users.CourseUser(**raw_object) for raw_object in raw_objects]
