import typing

import lms.model.users

# {course_name: {user_name: user, ...}, ...}
COURSE_USERS: typing.Dict[str, typing.Dict[str, lms.model.users.CourseUser]] = {}

COURSE_USERS['Course 101'] = {
    'course-admin': lms.model.users.CourseUser(
        email = 'course-admin@test.edulinq.org',
        id = '2',
        name = 'course-admin',
        role = lms.model.users.CourseRole.GRADER,
    ),
    'course-grader': lms.model.users.CourseUser(
        email = 'course-grader@test.edulinq.org',
        id = '3',
        name = 'course-grader',
        role = lms.model.users.CourseRole.GRADER,
    ),
    'course-other': lms.model.users.CourseUser(
        email = 'course-other@test.edulinq.org',
        id = '4',
        name = 'course-other',
        role = lms.model.users.CourseRole.OTHER,
    ),
    'course-owner': lms.model.users.CourseUser(
        email = 'course-owner@test.edulinq.org',
        id = '5',
        name = 'course-owner',
        role = lms.model.users.CourseRole.OWNER,
    ),
    'course-student': lms.model.users.CourseUser(
        email = 'course-student@test.edulinq.org',
        id = '6',
        name = 'course-student',
        role = lms.model.users.CourseRole.STUDENT,
    ),
}

COURSE_USERS['Course Using Different Languages'] = COURSE_USERS['Course 101']

COURSE_USERS['Extra Course'] = {
    'course-owner': COURSE_USERS['Course 101']['course-owner'],
    'extra-course-student-1': lms.model.users.CourseUser(
        email = 'extra-course-student-1@test.edulinq.org',
        id = '7',
        name = 'extra-course-student-1',
        role = lms.model.users.CourseRole.STUDENT,
    ),
    'extra-course-student-2': lms.model.users.CourseUser(
        email = 'extra-course-student-2@test.edulinq.org',
        id = '8',
        name = 'extra-course-student-2',
        role = lms.model.users.CourseRole.STUDENT,
    ),
    'extra-course-student-3': lms.model.users.CourseUser(
        email = 'extra-course-student-3@test.edulinq.org',
        id = '9',
        name = 'extra-course-student-3',
        role = lms.model.users.CourseRole.STUDENT,
    ),
    'extra-course-student-4': lms.model.users.CourseUser(
        email = 'extra-course-student-4@test.edulinq.org',
        id = '10',
        name = 'extra-course-student-4',
        role = lms.model.users.CourseRole.STUDENT,
    ),
}
