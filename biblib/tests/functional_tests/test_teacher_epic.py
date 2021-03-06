"""
Functional test

Teacher Epic

Storyboard is defined within the comments of the program itself
"""

import unittest
from flask import url_for
from biblib.views.http_errors import NO_PERMISSION_ERROR
from biblib.tests.stubdata.stub_data import UserShop, LibraryShop
from biblib.tests.base import MockEmailService, MockSolrBigqueryService, \
    TestCaseDatabase, MockEndPoint

class TestTeacherEpic(TestCaseDatabase):
    """
    Base class used to test the Teacher Epic
    """

    def test_teacher(self):
        """
        Carries out the epic 'Teacher', where a user wants to remove the
        privileges of one person, but not affect anyone else

        :return: no return
        """

        # Make the stub data required
        user_student_1 = UserShop()
        user_student_2 = UserShop()
        user_teacher = UserShop()
        stub_library = LibraryShop()

        # The teacher makes a library
        url = url_for('userview')
        response = self.client.post(
            url,
            data=stub_library.user_view_post_data_json,
            headers=user_teacher.headers
        )
        self.assertEqual(response.status_code, 200, response)
        library_id_teacher = response.json['id']

        # Some students complain that they cannot see the library that is
        # linked by the University web page
        # need a permissions endpoint
        # /permissions/<uuid_library>
        for user in [user_student_1, user_student_2]:
            # The students check they can see the content
            url = url_for('libraryview', library=library_id_teacher)
            with MockSolrBigqueryService(number_of_bibcodes=0) as BQ, \
                    MockEndPoint([
                        user_teacher, user_student_1, user_student_2
                    ]) as EP:
                response = self.client.get(
                    url,
                    headers=user.headers
                )
            self.assertEqual(
                response.status_code,
                NO_PERMISSION_ERROR['number']
            )
            self.assertEqual(
                response.json['error'],
                NO_PERMISSION_ERROR['body']
            )

        # The teacher adds two users with read permissions
        for user in [user_student_1, user_student_2]:
            # Permissions url
            url = url_for('permissionview', library=library_id_teacher)
            with MockEmailService(user):
                response = self.client.post(
                    url,
                    data=user.permission_view_post_data_json('read', True),
                    headers=user_teacher.headers
                )
            self.assertEqual(response.status_code, 200)

            # The students check they can see the content
            url = url_for('libraryview', library=library_id_teacher)
            with MockSolrBigqueryService(number_of_bibcodes=0) as BQ, \
                    MockEndPoint([
                        user_teacher, user_student_1, user_student_2
                    ]) as EP:
                response = self.client.get(
                    url,
                    headers=user.headers
                )
            self.assertEqual(response.status_code, 200)
            self.assertIn('documents', response.json)

        # The teacher realises student 2 is not in the class, and removes
        # the permissions, and makes sure student 1 can still see the content
        url = url_for('permissionview', library=library_id_teacher)
        with MockEmailService(user_student_2):
            response = self.client.post(
                url,
                data=user_student_2.permission_view_post_data_json('read',
                                                                   False),
                headers=user_teacher.headers
            )
        self.assertEqual(response.status_code, 200)

        # Student 2 cannot see the content
        url = url_for('libraryview', library=library_id_teacher)
        with MockSolrBigqueryService(number_of_bibcodes=0) as BQ, \
                MockEndPoint([
                    user_teacher, user_student_1, user_student_2
                ]) as EP:
            response = self.client.get(
                url,
                headers=user_student_2.headers
            )
        self.assertEqual(response.status_code, NO_PERMISSION_ERROR['number'])
        self.assertEqual(response.json['error'], NO_PERMISSION_ERROR['body'])

        # Student 1 can see the content still
        url = url_for('libraryview', library=library_id_teacher)
        with MockSolrBigqueryService(number_of_bibcodes=0) as BQ, \
                MockEndPoint([
                    user_teacher, user_student_1, user_student_2
                ]) as EP:
            response = self.client.get(
                url,
                headers=user_student_1.headers
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn('documents', response.json)

if __name__ == '__main__':
    unittest.main(verbosity=2)
