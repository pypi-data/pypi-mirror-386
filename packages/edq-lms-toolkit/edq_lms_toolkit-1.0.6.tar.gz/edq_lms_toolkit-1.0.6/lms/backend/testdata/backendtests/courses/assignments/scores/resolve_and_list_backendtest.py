import lms.backend.testing
import lms.model.courses
import lms.model.testdata.scores

def test_courses_assignments_scores_resolve_and_list_base(test: lms.backend.testing.BackendTest):
    """ Test the base functionality of resolving and listing assignments scores. """

    scores = lms.model.testdata.scores.COURSE_ASSIGNMENT_SCORES

    # [(kwargs (and overrides), expected, error substring), ...]
    test_cases = [
        (
            {
                'course_query': lms.model.courses.CourseQuery(id = '1'),
                'assignment_query': lms.model.assignments.AssignmentQuery(id = '1'),
            },
            [
                scores['Course 101']['Homework 0']['course-student'],
            ],
            None,
        ),

        (
            {
                'course_query': lms.model.courses.CourseQuery(name = 'Course 101'),
                'assignment_query': lms.model.assignments.AssignmentQuery(id = '1'),
            },
            [
                scores['Course 101']['Homework 0']['course-student'],
            ],
            None,
        ),

        (
            {
                'course_query': lms.model.courses.CourseQuery(id = '2'),
                'assignment_query': lms.model.assignments.AssignmentQuery(id = '2'),
            },
            [
            ],
            None,
        ),

        (
            {
                'course_query': lms.model.courses.CourseQuery(id = '3'),
                'assignment_query': lms.model.assignments.AssignmentQuery(id = '5'),
            },
            [
                scores['Extra Course']['Assignment 1']['extra-course-student-1'],
                scores['Extra Course']['Assignment 1']['extra-course-student-2'],
                scores['Extra Course']['Assignment 1']['extra-course-student-3'],
                scores['Extra Course']['Assignment 1']['extra-course-student-4'],
            ],
            None,
        ),

        (
            {
                'course_query': lms.model.courses.CourseQuery(id = '3'),
                'assignment_query': lms.model.assignments.AssignmentQuery(id = '6'),
            },
            [
                scores['Extra Course']['Assignment 2']['extra-course-student-1'],
                scores['Extra Course']['Assignment 2']['extra-course-student-2'],
                scores['Extra Course']['Assignment 2']['extra-course-student-3'],
                scores['Extra Course']['Assignment 2']['extra-course-student-4'],
            ],
            None,
        ),

        (
            {
                'course_query': lms.model.courses.CourseQuery(id = '3'),
                'assignment_query': lms.model.assignments.AssignmentQuery(id = '7'),
            },
            [
                scores['Extra Course']['Assignment 3']['extra-course-student-1'],
                scores['Extra Course']['Assignment 3']['extra-course-student-2'],
                scores['Extra Course']['Assignment 3']['extra-course-student-3'],
            ],
            None,
        ),
    ]

    test.base_request_test(test.backend.courses_assignments_scores_resolve_and_list, test_cases)
