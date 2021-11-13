'''User views tests'''

import logging
import os
from unittest import TestCase
from flask import url_for, request, session, g
from time import sleep

from models import db, User, Message, Follow, Like
from test_user_model import create_test_user
from sqlalchemy.exc import IntegrityError
from custom_exceptions import UsernameAlreadyExistsError, EmailAlreadyExistsError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app, CURR_USER_KEY

# Use test database and don't clutter tests with SQL
app.config['SQLALCHEMY_ECHO'] = False

# Make Flask errors be real errors, rather than HTML pages with error info
app.config['TESTING'] = True

# don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# disable CSRF checking
app.config['WTF_CSRF_ENABLED'] = False

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
db.drop_all()
db.create_all()

class UserViewsTestCase(TestCase):
    '''Base class for testing user views.'''

    def setUp(self):
        '''Create a test client.'''
        
        self.app_context = app.test_request_context()
        self.app_context.push()
        self.client = app.test_client()

        User.query.delete()

        self.user_data = {
            'email': 'test@test.com',
            'username': 'testuser',
            'password': 'PASSWORD',
            'image_url': None
        }

    def tearDown(self):
        '''Clean up fouled transactions.'''

        db.session.rollback()
        # self.app_context.pop()


class UserSignupViewTestCase(UserViewsTestCase):
    '''Test the user signup view.'''

    def test_signup_form(self):
        '''
        Test that the signup form is displayed on a GET request to the signup route.
        '''
       
        resp = self.client.get(url_for('signup'))

        self.assertEqual(resp.status_code, 200)

        html = resp.get_data(as_text=True)

        form_markup = '<form method="POST" id="user_form">'
        signup_btn = '<button class="btn btn-primary btn-lg btn-block">Sign me up!</button>'

        for component in [form_markup, signup_btn, 'username', 'password', 'email', 'image_url']:
            self.assertIn(component, html)

    def test_signup_submit(self):
        '''
        Test that a new user is added to the database and the user is redirected to 
        the homepage on a POST request to the signup route.
        '''

        resp = self.client.post(url_for('signup'), data=self.user_data, follow_redirects=True)

        # test 200 ok status and successful redirect to homepage
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(request.path, url_for('homepage'))

        # test flash msg
        html = resp.get_data(as_text=True)
        welcome_msg = f"Welcome to Warbler {self.user_data['username']}!"
        self.assertIn(welcome_msg, html)

        # test user succesfully added
        self.assertEqual(User.query.count(), 1)

        # test that user id is added to session obj FIX
        # self.assertEqual(session.get(CURR_USER_KEY), g.user.id)

    # def test_signup_username_taken(self):
    #     '''
    #     Test that an error message is flashed and the user is shown the form again 
    #     when attempting to signup with a username that is already registered. 
    #     '''

    #     # add user to db with hashed pw
    #     user = User.signup(**self.user_data)

    #     self.user_data['email'] = 'diff@gmail.com' # change to diff email
    #     # sign up a user with same username
    #     resp = self.client.post(url_for('signup'), data=self.user_data, follow_redirects=True)

    #     self.assertEqual(resp.status_code, 200)

    #     html = resp.get_data(as_text=True)
    #     msg = f'Username {user.username} is taken.'
    #     form_markup = '<form method="POST" id="user_form">'

    #     for component in [msg, form_markup]:
    #         self.assertIn(component, html)

    

class UserLoginLogoutViewsTestCase(UserViewsTestCase):
    '''Test user login and logout views.'''

    def setUp(self):
        '''Create a test client and user.'''
    
        # create a test client
        super().setUp()

        self.user = User.signup(**self.user_data)

    def test_login_form(self):
        '''
        Test that the login form is displayed on a GET request to the login route.
        '''
       
        resp = self.client.get(url_for('login'))

        self.assertEqual(resp.status_code, 200)

        html = resp.get_data(as_text=True)

        form_markup = '<form method="POST" id="user_form">'
        login_btn = '<button class="btn btn-primary btn-block btn-lg">Log in</button>'

        for component in [form_markup, login_btn, 'username', 'password']:
            self.assertIn(component, html)

    def test_login_submit_valid(self):
        '''
        Test that a user is successfully authenticated and redirected to 
        the homepage on a POST request to the login route.
        '''

        # login user
        login_creds = {'username': self.user_data['username'], 'password': self.user_data['password']}
        resp = self.client.post(url_for('login'), data=login_creds, follow_redirects=True)

        # test 200 ok status and successful redirect to homepage
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(request.path, url_for('homepage'))

        # test flash msg
        html = resp.get_data(as_text=True)
        welcome_msg = f"Hello, {self.user_data['username']}!"
        self.assertIn(welcome_msg, html)

        # test that user id is added to session obj FIX
        #self.assertEqual(session.get(CURR_USER_KEY), self.user.id)

    def test_login_submit_invalid_username(self):
        '''
        Test that a user with an invalid username is not logged.
        '''

        # login user with invalid username
        login_creds = {'username': 'invalid', 'password': self.user_data['password']}
        resp = self.client.post(url_for('login'), data=login_creds, follow_redirects=True)
        
        self.assertEqual(resp.status_code, 200)

        # test flash msg
        html = resp.get_data(as_text=True)
        msg = 'Invalid credentials'
        self.assertIn(msg, html)

    def test_login_submit_invalid_password(self):
        '''
        Test that a user with an invalid password is not logged.
        '''

        # login user with invalid username
        login_creds = {'username': self.user_data['username'], 'password': 'invalid'}
        resp = self.client.post(url_for('login'), data=login_creds, follow_redirects=True)
        
        self.assertEqual(resp.status_code, 200)

        # test flash msg
        html = resp.get_data(as_text=True)
        msg = 'Invalid credentials'
        self.assertIn(msg, html)

    def test_logout(self):
        '''
        Test that a user is successfully logged out and redirected to the login page.
        '''

        # add user_id to session, so user is "logged in"
        with self.client.session_transaction() as change_session:
            change_session[CURR_USER_KEY] = self.user.id

            # log out user
            resp = self.client.get(url_for('logout'), follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(request.path, url_for('login'))

            html = resp.get_data(as_text=True)
            logout_msg = "You've been logged out."
            
            # check that logout message is displayed
            self.assertIn(logout_msg, html)

            # check that session and g are cleared
            self.assertNotIn(CURR_USER_KEY, session)
            self.assertIsNone(g.user)


class UserGeneralViewsTestCase(UserViewsTestCase):
    '''Test general user views.'''

    def setUp(self):
        '''Create a test client and user.'''
    
        # create a test client
        super().setUp()

        # create 1st user
        self.user1 = User.signup(**self.user_data)

        # create 2nd user_data by prepending '2' to user1's data
        self.user_data2 = {k: '2' + v if v else None for k, v in self.user_data.items()}
        self.user2 = User.signup(**self.user_data2)

    def test_list_users_all(self):
        '''Test that the list_users route displays a list of all users
        when given no search param.'''

        resp = self.client.get(url_for('list_users'))

        self.assertEqual(resp.status_code, 200)

        html = resp.get_data(as_text=True) 

        # for user in [self.user1.username, self.user2.username]:
        #     self.assertIn(user, html)   

        self.assertEqual(User.query.count(), 2)

    def test_list_users_with_search_param(self):
        '''
        Test that the list_users route displays a list of all users 
        with a username that matches the given search param.
        '''

        # search for user2
        resp = self.client.get(url_for('list_users'), query_string={'q': '2'})

        self.assertEqual(resp.status_code, 200)

        html = resp.get_data(as_text=True) 

        # test that user2 shows up
        self.assertIn(f'Image for {self.user2.username}', html)
        # test that user1 does not show up 
        self.assertNotIn(f'Image for {self.user1.username}', html)

    def test_list_users_empty(self):
        '''Test that no users are displayed if search param matches no users.'''

        resp = self.client.get(url_for('list_users'), query_string={'q': 'xyzabc'})

        self.assertEqual(resp.status_code, 200)

        html = resp.get_data(as_text=True) 

        msg = '<h3>Sorry, no users found</h3>'
        self.assertIn(msg, html)
        for user in [self.user1, self.user2]:
            self.assertNotIn(user.username, html)

    def test_users_show(self):
        '''Test that the users's profile is displayed with their messages (100 max)
        listed in order with the most recent at the top.'''

        MAX_MESSAGES = 100

        # add 101 messages to user1
        MESSAGE_DATA = {'text': 'A message', 'user_id': self.user1.id}
        newest_msg = 'Newest message.'
        oldest_msg = 'Oldest message.'
        for msg in range(MAX_MESSAGES + 1):
            if msg == 0: # oldest msg (won't be displayed due to 100 limit max)
                self.user1.messages.append(Message(text=oldest_msg, user_id=self.user1.id))
            elif msg == 100: # most recent msg
                self.user1.messages.append(Message(text=newest_msg, user_id=self.user1.id))
            else:
                self.user1.messages.append(Message(**MESSAGE_DATA))

        resp = self.client.get(url_for('users_show', user_id=self.user1.id))

        self.assertEqual(resp.status_code, 200)

        html = resp.get_data(as_text=True)

        # test that no more than 100 messages are displayed
        num_messages_displayed = html.count('<li class="list-group-item">') 
        self.assertEqual(num_messages_displayed, MAX_MESSAGES)

        # test that the newest message is displayed
        self.assertIn(newest_msg, html)
        # test that the oldest message is not displayed
        self.assertNotIn(oldest_msg, html)

    def test_show_following(self):
        '''
        Test that the 'show_following' route displays all users that 
        a given user is following.
        '''
        # add a 3rd and 4th user
        user4 = User.signup(username='fourthuser', email='f@gmail.com', password='123', image_url=None)
        user3 = User.signup(username='thirduser', email='t@gmail.com', password='123', image_url=None)
        
        # log user3 in 
        with self.client.session_transaction() as change_session:
            change_session[CURR_USER_KEY] = user3.id
            
        # make user1 follow user2, user3, user4
        self.user1.following.extend([self.user2, user3, user4])
        db.session.add(self.user1)

        # make user3 follow user4
        user3.following.append(user4)
        db.session.add(user3)
        db.session.commit()

        # show who user1 is following
        resp = self.client.get(url_for('show_following', user_id=self.user1.id))
        
        self.assertEqual(resp.status_code, 200)

        html = resp.get_data(as_text=True)

        # test that unfollow button is displayed for user4 (user3 is following user4)
        unfollow_btn = '<button class="btn btn-primary btn-sm">Unfollow</button>'
        self.assertIn(unfollow_btn, html)
        
        # test that follow button is displayed for user2 (user3 is not following user2)
        follow_btn = '<button class="btn btn-outline-primary btn-sm">Follow</button>'
        self.assertIn(follow_btn, html)

        # test that user2, user3, user4 are displayed (users whom user1 follows)
        for user in [self.user2, user3, user4]:
            self.assertIn(user.username, html)
  
    def test_show_following_unauth(self):
        '''
        Test that the 'show_following' route redirects to the homepage 
        and that an access unauthorized message is displayed if user is logged out.
        '''

        # attempt to access page listing users whom user1 follows
        resp = self.client.get(url_for('show_following', user_id=self.user1.id), follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(request.path, url_for('homepage'))

        html = resp.get_data(as_text=True)
        unauth_msg = 'Access unauthorized.'

        self.assertIn(unauth_msg, html)

    def test_show_followers(self):
        '''
        Test that a list of the given user's followers is displayed.
        '''

         # add a 3rd and 4th user
        user4 = User.signup(username='fourthuser', email='f@gmail.com', password='123', image_url=None)
        user3 = User.signup(username='thirduser', email='t@gmail.com', password='123', image_url=None)
        
        # log user3 in 
        with self.client.session_transaction() as change_session:
            change_session[CURR_USER_KEY] = user3.id
            
        # make user2, user3, and user4 follow user1
        self.user1.followers.extend([self.user2, user3, user4])
        db.session.add(self.user1)

        # make user3 follow user4
        user3.following.append(user4)
        db.session.add(user3)
        db.session.commit()

        # show user1's followers
        resp = self.client.get(url_for('show_followers', user_id=self.user1.id))
        
        self.assertEqual(resp.status_code, 200)

        html = resp.get_data(as_text=True)

        # test that unfollow button is displayed for user4 (user3 is following user4)
        unfollow_btn = '<button class="btn btn-primary btn-sm">Unfollow</button>'
        self.assertIn(unfollow_btn, html)
        
        # test that follow button is displayed for user2 (user3 is not following user2)
        follow_btn = '<button class="btn btn-outline-primary btn-sm">Follow</button>'
        self.assertIn(follow_btn, html)

        # test that user2, user3, user4 are displayed (user1's followers)
        for user in [self.user2, user3, user4]:
            self.assertIn(user.username, html)

    def test_show_followers_unauth(self):
        '''
        Test that the 'show_followers' route redirects to the homepage 
        and that an access unauthorized message is displayed if user is logged out.
        '''

        # attempt to access user1's followers page
        resp = self.client.get(url_for('show_followers', user_id=self.user1.id), follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(request.path, url_for('homepage'))

        html = resp.get_data(as_text=True)
        unauth_msg = 'Access unauthorized.'

        self.assertIn(unauth_msg, html)

    def test_start_following(self):
        '''
        Test that the 'start_following' route adds the logged-in-user
        as a follower of the given user and that the logged-in-user
        is redirected to the page of users they follow.
        '''
        # FIX WHOLE METHOD REDIRECTING TO UNAUTHORIZED DESPITE LOGIN
        # log user1 in 
        with self.client.session_transaction() as change_session:
            change_session[CURR_USER_KEY] = self.user1.id

        # have user1 follow user2
        resp = self.client.post(url_for('start_following', follow_id=self.user2.id))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(request.path, url_for('show_following', user_id=self.user1.id))

        html = resp.get_data(as_text=True)

        # test that user2 is displayed in user1's followings page
        self.assertIn(self.user2.username, html)

        # test that user2 is in user1's followings list
        self.assertIn(self.user2, self.user1.following)

    def test_start_following_unauth(self):
        '''
        Test that the 'start_following' route redirects to the homepage 
        and that an access unauthorized message is displayed if user is logged out.
        '''

        # attempt to follow user2
        resp = self.client.post(url_for('start_following', follow_id=self.user2.id), follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(request.path, url_for('homepage'))

        html = resp.get_data(as_text=True)
        unauth_msg = 'Access unauthorized.'

        self.assertIn(unauth_msg, html)

    def test_stop_following(self):
        '''
        Test that the 'stop_following' route removes the logged-in-user
        as a follower of the given user and that the logged-in-user
        is redirected to the page of users they follow.
        '''
        # FIX WHOLE METHOD REDIRECTING TO UNAUTHORIZED DESPITE LOGIN
        # have user1 follow user2
        self.user1.following.append(self.user2)

        # log user1 in 
        with self.client.session_transaction() as change_session:
            change_session[CURR_USER_KEY] = self.user1.id

        # have user1 stop following user2
        resp = self.client.post(url_for('stop_following', follow_id=self.user2.id))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(request.path, url_for('show_following', user_id=self.user1.id))

        html = resp.get_data(as_text=True)

        # test that user2 is not displayed in user1's followings page
        self.assertNotIn(self.user2.username, html)

        # test that user2 is in user1's followings list
        self.assertNotIn(self.user2, self.user1.following)

    def test_stop_following_unauth(self):
        '''
        Test that the 'stop_following' route redirects to the homepage 
        and that an access unauthorized message is displayed if user is logged out.
        '''

        # attempt to follow user2
        resp = self.client.post(url_for('stop_following', follow_id=self.user2.id), follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(request.path, url_for('homepage'))

        html = resp.get_data(as_text=True)
        unauth_msg = 'Access unauthorized.'

        self.assertIn(unauth_msg, html)

    def test_profile_display(self):
        '''
        Test that the user's profile page:
        1. displays their location, bio, and header image
        '''

        # add location and bio to user1
        self.user1.bio = "user's bio"
        self.user1.location = "user's location"
        db.session.add(self.user1)
        db.session.commit()

        # log user1 in 
        with self.client.session_transaction() as change_session:
            change_session[CURR_USER_KEY] = self.user1.id

        # go to user1's profile page
        resp = self.client.get(url_for('profile'))

        self.assertEqual(resp.status_code, 200)

        html = resp.get_data(as_text=True)

        self.assertIn(self.user1.username, html)
        self.assertIn(self.user1.bio, html)
        self.assertIn(self.user1.location, html)
        self.assertIn(self.user1.header_image_url, html)
        







    





    







    