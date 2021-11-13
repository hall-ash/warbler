'''Message model tests.'''

import os
from unittest import TestCase

from models import db, User, Message, Follow, Like
from test_user_model import create_test_user
from sqlalchemy.exc import IntegrityError, DataError
from datetime import datetime
from copy import deepcopy

os.environ['DATABASE_URL'] = 'postgresql:///warbler-test'

from app import app

db.create_all()

def create_test_message(data):
    '''Create and return a message instance'''
    m = Message(**data)
    db.session.add(m)
    db.session.commit()
    return m

class MessageModelTestCase(TestCase):
    '''Test the message model.'''

    def setUp(self):
        """Create test client, add sample data."""  

        for model in [User, Message, Follow, Like]:
            model.query.delete()

        self.client = app.test_client()

        self.msg_creator = create_test_user()

        self.msg_data = {
            'text': 'This is the message text.',
            'user_id': self.msg_creator.id
        }

    def tearDown(self):
        '''Clean up fouled transactions.'''

        db.session.rollback()

    def test_message_model(self):
        '''Test that a message is created with correct data.'''

        m = create_test_message(self.msg_data)

        # test that Message attributes are correct
        self.assertIsInstance(m.id, int)
        self.assertEqual(m.text, self.msg_data['text'])
        self.assertIsInstance(m.timestamp, datetime)
        self.assertEqual(m.user_id, self.msg_creator.id)
        self.assertIs(m.user, self.msg_creator)

    def test_repr(self):
        '''Test that the __repr__ method displays the message's id and its creator's user id.'''

        m = create_test_message(self.msg_data)

        repr_str = repr(m)

        self.assertIn(str(m.id), repr_str)
        self.assertIn(str(self.msg_creator.id), repr_str)


    def test_non_nullable_constraints(self):
        '''Test that an IntegrityError is raised if text, timestamp, or user_id is not provided.'''

        create_test_message(self.msg_data)

        # create msg data with no text 
        no_text_data = deepcopy(self.msg_data)
        no_text_data['text'] = None

        # create msg data with no user_id 
        no_user_id_data = deepcopy(self.msg_data)
        no_user_id_data['user_id'] = None

        for missing_data in [no_text_data, no_user_id_data]:
            self.assertRaises(IntegrityError, create_test_message, missing_data)
            db.session.rollback()

    def test_text_length_constraint(self):
        '''Test that an DataError is raised if text is longer than 140 characters.'''

        long_text = 141 * 'a'

        self.assertRaises(DataError, create_test_message, {'text': long_text, 'user_id': self.msg_creator.id})

    def test_text_max_length(self):
        '''Test that a message with the maximum length of 140 characters is successfully created.'''
        MAX_LENGTH = 140

        max_text = MAX_LENGTH * 'a'

        m = create_test_message({'text': max_text, 'user_id': self.msg_creator.id})

        self.assertIsInstance(m, Message)
        self.assertEqual(m.text, max_text)

    
        


