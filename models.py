"""SQLAlchemy models for Warbler."""

from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from custom_exceptions import UsernameAlreadyExistsError, EmailAlreadyExistsError
import logging

logging.basicConfig(filename='model-errors.log')

bcrypt = Bcrypt()
db = SQLAlchemy()


class Follow(db.Model):
    """Connection of a follower <-> followed_user."""

    __tablename__ = 'follows'

    user_being_followed_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

    user_following_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

    def __repr__(self):
        return f"<Follow followed={self.user_being_followed_id}, follower={self.user_following_id}>"


class Like(db.Model):
    """Mapping user likes to warbles."""

    __tablename__ = 'likes' 

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade')
    )

    message_id = db.Column(
        db.Integer,
        db.ForeignKey('messages.id', ondelete='cascade'),
        unique=True
    )

    def __repr__(self):
        return f"<Like id={self.id}, message_id={self.message_id}, user_id={self.user_id}>"


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    image_url = db.Column(
        db.Text,
        default="/static/images/default-pic.png",
    )

    header_image_url = db.Column(
        db.Text,
        default="/static/images/warbler-hero.jpg"
    )

    bio = db.Column(
        db.Text,
    )

    location = db.Column(
        db.Text,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    messages = db.relationship('Message')

# SELECT username AS follower
# FROM users
# JOIN follows
# ON follows.user_following_id = users.id
# WHERE follows.user_being_followed_id = 1;

    followers = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follow.user_being_followed_id == id),
        secondaryjoin=(Follow.user_following_id == id)
    )

    following = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follow.user_following_id == id),
        secondaryjoin=(Follow.user_being_followed_id == id)
    )

    likes = db.relationship(
        'Message',
        secondary="likes"
    )

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    def is_followed_by(self, other_user_id):
        """Is this user followed by `other_user`?"""
        is_followed_by = Follow.query.filter_by(user_being_followed_id=self.id, user_following_id=other_user_id).first() 
        
        return bool(is_followed_by)

        # found_user_list = [user for user in self.followers if user == other_user]
        # return len(found_user_list) == 1

    def is_following(self, other_user_id):
        """Is this user following `other_use`?"""

        is_following = Follow.query.filter_by(user_being_followed_id=other_user_id, user_following_id=self.id).first()

        return bool(is_following)
        
        # found_user_list = [user for user in self.following if user == other_user]
        # return len(found_user_list) == 1

    def get_all_msgs(self, limit=100):
        '''
        Get messages from the user and the users that the user is following. 
        Returns at most 'limit' messages ordered by most recent first.
        '''

        msgs_from_following = Message.query.join(Follow, Message.user_id == Follow.user_being_followed_id).filter(Follow.user_following_id == self.id)
        own_msgs = Message.query.filter_by(user_id = self.id)

        return msgs_from_following.union_all(own_msgs).order_by(Message.timestamp.desc()).limit(limit).all()

    @classmethod
    def signup(cls, username, email, password, image_url):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)

        try: 
            db.session.commit()
             # is there a reason db.session.commit() is not in this method
            return user

        except Exception as e:
            logging.exception(e)
            if 'users_username_key' in str(e):
                raise UsernameAlreadyExistsError(username=user.username)
            elif 'users_email_key' in str(e):
                raise EmailAlreadyExistsError(email=user.email)
            else:
                raise e

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        try:
            user = cls.query.filter_by(username=username).one_or_none()
        except Exception as e:
            logging.exception(e)
            raise e

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


class Message(db.Model):
    """An individual message ("warble")."""

    __tablename__ = 'messages'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    text = db.Column(
        db.String(140),
        nullable=False,
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    user = db.relationship('User')

    def __repr__(self):
        return f"<Message id={self.id}, user_id={self.user_id}>"


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)

