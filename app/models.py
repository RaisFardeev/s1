from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from . import db


class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))
    email = Column(String(30), unique=True, nullable=False)
    password = Column(String(20))
    token = Column(String(100), unique=True)
    balance = Column(Integer, default=0)


class Ad(db.Model):
    __tablename__ = 'ads'
    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
    uploaded = Column(DateTime, nullable=False, default=func.now())
    name = Column(String(50), nullable=False)
    description = Column(String(300), nullable=False)
    preordered = Column(Boolean, default=False)
    bought = Column(Boolean, default=False)
    price = Column(Integer, nullable=False)
    category = Column(String(20), default='no category')
    creator = relationship('User', backref='ads')


class Photo(db.Model):
    __tablename__ = 'photo'
    ad_id = Column(Integer, ForeignKey('ads.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True)
    path = Column(String, nullable=False)
    ad = relationship('Ad', backref='photos')


class LikedAd(db.Model):
    __tablename__ = 'liked_ads'
    ad_id = Column(Integer, ForeignKey('ads.id', ondelete='CASCADE'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)


class BoughtAd(db.Model):
    __tablename__ = 'bought_ads'
    ad_id = Column(Integer, ForeignKey('ads.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, nullable=False)