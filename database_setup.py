import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    id = Column(Integer, primary_key=True)


class Lens(Base):
    __tablename__ = 'lens'

    id = Column(Integer, primary_key=True)
    name = Column(String(350), nullable=False)
    brand = Column(String(80))
    style = Column(String(80))
    zoom_min = Column(String(80))
    zoom_max = Column(String(80))
    aperture = Column(String(80))
    price_per_day = Column(String(8))
    price_per_week = Column(String(8))
    price_per_month = Column(String(8))
    picture = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship(User)

    @property
    def serialize(self):

        return {
            'id': self.id,
            'name': self.name,
            'brand': self.brand,
            'style': self.style,
            'zoom_min': self.zoom_min,
            'zoom_max': self.zoom_max,
            'aperture': self.aperture,
            'price_per_day': self.price_per_day,
            'price_per_week': self.price_per_week,
            'price_per_month': self.price_per_month,
        }


class Rental(Base):
    __tablename__ = 'rental'

    id = Column(Integer, primary_key=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    renter_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    lens_id = Column(Integer, ForeignKey('lens.id'), nullable=False)
    renter = relationship("User", foreign_keys=[renter_id])
    owner = relationship("User", foreign_keys=[owner_id])
    lens = relationship(Lens)


engine = create_engine('sqlite:///sharealens.db')


Base.metadata.create_all(engine)
