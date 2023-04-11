from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False)
    email = Column(String(30), unique=True, nullable=False)
    password = Column(String(20), nullable=False)
    balance = Column(Integer, default=0)


class Ad(Base):
    __tablename__ = 'ads'
    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
    uploaded = Column(String, nullable=False, server_default='CURRENT_TIMESTAMP')
    name = Column(String(50), nullable=False)
    description = Column(String(300), nullable=False)
    preordered = Column(Boolean, default=False)
    bought = Column(Boolean, default=False)
    price = Column(Integer, nullable=False)
    category = Column(String(20), default='no category')
    creator = relationship('User', backref='ads')


class Photo(Base):
    __tablename__ = 'photo'
    ad_id = Column(Integer, ForeignKey('ads.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True)
    path = Column(String, nullable=False)
    ad = relationship('Ad', backref='photos')


class LikedAd(Base):
    __tablename__ = 'liked_ads'
    ad_id = Column(Integer, ForeignKey('ads.id', ondelete='CASCADE'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)


class BoughtAd(Base):
    __tablename__ = 'bought_ads'
    ad_id = Column(Integer, ForeignKey('ads.id', ondelete='CASCADE'), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)