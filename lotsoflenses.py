from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Lens, User

engine = create_engine('sqlite:///sharealens.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

#Create user
User1 = User(
       name="Joe McPhotographer",
       email="joe-takes-photos@gmail.com",
       picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

#Create lenses.  All owned by user 1
lens1 = Lens(
       user_id=1,
       name="Canon EF 50mm f/1.8 II Camera Lens",
       brand="Canon",
       style="Portrait",
       zoom_min="50mm",
       zoom_max="50mm",
       aperture="1.8",
       price_per_day="$10.00",
       price_per_week="$50.00",
       price_per_month="$150.00",
       picture="1/1.jpg")

session.add(lens1)
session.commit()


lens2 = Lens(
       user_id=1,
       name="Canon EF-S 55-250mm F/4-5.6 IS STM Telephoto Zoom Lens",
       brand="Canon",
       style="Telephoto",
       zoom_min="55mm",
       zoom_max="250mm",
       aperture="4-5.6",
       price_per_day="$13.00",
       price_per_week="$60.00",
       price_per_month="$190.00",
       picture="2/1.jpg")

session.add(lens2)
session.commit()


lens3 = Lens(
       user_id=1,
       name="NIKON 14mm f/2.8D ED AF Ultra Wide-Angle Nikkor Lens",
       brand="Nikon",
       style="Ultra Wide",
       zoom_min="14mm",
       zoom_max="14mm",
       aperture="2.8",
       price_per_day="$35.00",
       price_per_week="$210.00",
       price_per_month="$480.00",
       picture="3/1.jpg")

session.add(lens3)
session.commit()


lens4 = Lens(
       user_id=1,
       name="Canon EF 100-400mm f/4.5-5.6L IS USM Telephoto Zoom Lens for Canon SLR Cameras",
       brand="Canon",
       style="Telephoto",
       zoom_min="100mm",
       zoom_max="400mm",
       aperture="4.5-5.6",
       price_per_day="$33.00",
       price_per_week="$210.00",
       price_per_month="$480.00",
       picture="4/1.jpg")

session.add(lens4)
session.commit()


print "added lenses!"