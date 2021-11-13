"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from copy import deepcopy
from unittest import TestCase

from models import db, User, Message, Follow, Like
from sqlalchemy.exc import IntegrityError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

USER_DATA = {
    'email': 'test@test.com',
    'username': 'testuser',
    'password': 'PASSWORD',
    'image_url': None
}

USER_DATA2 = {
    'email': 'test@test2.com',
    'username': 'testuser2',
    'password': 'PASSWORD',
    'image_url': None
}

DEFAULT_IMG_URL = "/static/images/default-pic.png"
DEFAULT_HEADER_IMG_URL = "/static/images/warbler-hero.jpg"

def create_test_user(data=None):
    '''Create and return a user instance.'''

    if not data:
        data = {
            'email': 'test@test.com',
            'username': 'testuser',
            'password': 'PASSWORD',
            'image_url': None
        }

    u = User(**data)
    db.session.add(u)
    db.session.commit()
    return u

class UserModelTestCase(TestCase):
    """Test the User model."""

    def setUp(self):
        """Create test client, add sample data."""

        for model in [User, Message, Follow, Like]:
            model.query.delete()

        self.client = app.test_client()

    def tearDown(self):
        '''Clean up fouled transactions.'''
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = create_test_user(USER_DATA)

        # test that User attributes are correct
        self.assertIsInstance(u.id, int)
        self.assertEqual(u.email, USER_DATA['email'])
        self.assertEqual(u.username, USER_DATA['username'])
        
        # test that default images are provided
        self.assertEqual(u.image_url, DEFAULT_IMG_URL)
        self.assertEqual(u.header_image_url, DEFAULT_HEADER_IMG_URL)
        self.assertEqual(u.password, USER_DATA['password'])

        # User should have no messages, likes, followers, or followings
        for attr in [u.messages, u.likes, u.followers, u.following]:
            self.assertEqual(len(attr), 0)
   

    def test_repr(self):
        '''Test that the __repr__ method displays the user's id, username, and email.'''

        u = create_test_user(USER_DATA)

        repr_str = repr(u)

        self.assertIn(str(u.id), repr_str)
        self.assertIn(u.username, repr_str)
        self.assertIn(u.email, repr_str)

    def test_signup(self):
        '''Test that signup() hashes the password and adds the user to the database.'''

        u = User.signup(**USER_DATA)

        # test that hashed password is stored
        self.assertNotEqual(USER_DATA['password'], u.password)

        # test that user is added to the db
        self.assertEqual(User.query.count(), 1)

    def test_signup_unique_constraints(self):
        '''Test that signup() fails when username and/or email are not unique.'''

        User.signup(**USER_DATA)

        # create user data with same username 
        same_username_data = deepcopy(USER_DATA2)
        same_username_data['username'] = USER_DATA['username']

        # create user data with same email 
        same_email_data = deepcopy(USER_DATA2)
        same_email_data['email'] = USER_DATA['email']

        for non_unique_data in [same_username_data, same_email_data, USER_DATA]:
            self.assertRaises(IntegrityError, User.signup, **non_unique_data)
            db.session.rollback()

    def test_signup_non_nullable_constraints(self):
        '''Test that signup() fails when username, email, or password are not provided.'''

        # create user data with no username 
        no_username_data = deepcopy(USER_DATA)
        no_username_data['username'] = None

        # create user data with no email 
        no_email_data = deepcopy(USER_DATA)
        no_email_data['email'] = None

        # create user data with no password 
        no_pass_data = deepcopy(USER_DATA)
        no_pass_data['password'] = None

        for missing_data in [no_username_data, no_email_data]:
            self.assertRaises(IntegrityError, User.signup, **missing_data)
            db.session.rollback()

        self.assertRaises(ValueError, User.signup, **no_pass_data)

        
    def test_authenticate_valid_user_creds(self):
        '''Test that authenticate() returns the user instance when given valid credentials.'''

        # sign up a user
        User.signup(**USER_DATA)

        auth_user = User.authenticate(USER_DATA['username'], USER_DATA['password'])

        self.assertIsInstance(auth_user, User)

    def test_authenticate_invalid_user_creds(self):
        '''Test that authenticate() returns False when given an invalid username and/or password.'''

        # sign up a user
        User.signup(**USER_DATA)

        invalid_username = User.authenticate('invalid_username', USER_DATA['password'])
        invalid_password = User.authenticate(USER_DATA['username'], 'invalid_password')
        invalid_username_and_pass = User.authenticate('invalid_username', USER_DATA['password'])

        for invalid_creds in [invalid_username, invalid_password, invalid_username_and_pass]:
            self.assertFalse(invalid_creds)

    def test_unique_username(self):
        '''Test that an IntegrityError is raised if username is not unique.'''

        # add first user
        create_test_user(USER_DATA)

        # create second user with identical username
        copied_data = deepcopy(USER_DATA)
        copied_data['email'] = 'different@test.com'
      
        self.assertRaises(IntegrityError, create_test_user, copied_data)

    def test_email_unique(self):
        '''Test that an IntegrityError is raised if email is not unique.'''

        # add first user
        create_test_user(USER_DATA)

        # create second user with identical email
        copied_data = deepcopy(USER_DATA)
        copied_data['username'] = 'different'
      
        self.assertRaises(IntegrityError, create_test_user, copied_data)
        

    def test_is_followed_by(self):
        '''Test that is_followed_by() returns True if the user is followed by other_user and False otherwise.'''

        u1 = create_test_user(USER_DATA)
        u2 = create_test_user(USER_DATA2)

        self.assertFalse(u1.is_followed_by(u2.id))

        # add u2 to u1's followers
        u1.followers.append(u2)

        self.assertTrue(u1.is_followed_by(u2.id))

    def test_is_following(self):
        '''Test that is_following() returns True if the user is following other_user and False otherwise.'''

        u1 = create_test_user(USER_DATA)
        u2 = create_test_user(USER_DATA2)

        self.assertFalse(u1.is_following(u2.id))

        # add u2 to the users that u1 is following
        u1.following.append(u2)

        self.assertTrue(u1.is_following(u2.id))

    def test_msgs_cascade_delete(self):
        '''Test that all of a user's messages will be deleted upon user deletion.'''
        
        u = create_test_user(USER_DATA)
        text = 'This is the message text'

        # add 3 messages created by u
        for _ in range(3):
            u.messages.append(Message(text=text, user_id=u.id))
        
        db.session.add(u)
        db.session.commit()

        # assert that there are 3 messages in the db
        self.assertEqual((len(u.messages)), 3)

        # delete the user
        db.session.delete(u)
        db.session.commit()

        # assert that all messages by u have been deleted
        self.assertEqual(Message.query.filter_by(user_id=u.id).count(), 0)

