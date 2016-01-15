from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Lens, User, Rental

import datetime

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

# Create user
User1 = User(
       name="Joe McPhotographer",
       email="joe-takes-photos@gmail.com",
       picture='https://pbs.twimg.com/profile_images/2671170543/' +
               '18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# Create user
User2 = User(
       name="Johnny RentsAlot",
       email="Johnny-rents-lenses@gmail.com",
       picture='https://pbs.twimg.com/profile_images/2671170543/' +
               '18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User2)
session.commit()

# Create lenses.  All owned by user 1
lens1 = Lens(
       user_id=1,
       name="Canon EF 50mm f/1.8 II Camera Lens",
       brand="Canon",
       style="Prime",
       zoom_min="50",
       zoom_max="50",
       aperture="1.8",
       price_per_day="10.00",
       price_per_week="50.00",
       price_per_month="150.00",
       picture="1/1.jpg")

session.add(lens1)
session.commit()


lens2 = Lens(
       user_id=1,
       name="Canon EF-S 55-250mm F/4-5.6 IS STM Telephoto Zoom Lens",
       brand="Canon",
       style="Telephoto",
       zoom_min="55",
       zoom_max="250",
       aperture="4-5.6",
       price_per_day="13.00",
       price_per_week="60.00",
       price_per_month="190.00",
       picture="2/1.jpg")

session.add(lens2)
session.commit()


lens3 = Lens(
       user_id=1,
       name="NIKON 14mm f/2.8D ED AF Ultra Wide-Angle Nikkor Lens",
       brand="Nikon",
       style="Wide Angle",
       zoom_min="14",
       zoom_max="14",
       aperture="2.8",
       price_per_day="35.00",
       price_per_week="210.00",
       price_per_month="480.00",
       picture="3/1.jpg")

session.add(lens3)
session.commit()


lens4 = Lens(
       user_id=1,
       name="Canon EF 100-400mm f/4.5-5.6L IS USM Telephoto Zoom Lens" +
            " for Canon SLR Cameras",
       brand="Canon",
       style="Telephoto",
       zoom_min="100",
       zoom_max="400",
       aperture="4.5-5.6",
       price_per_day="33.00",
       price_per_week="210.00",
       price_per_month="480.00",
       picture="4/1.jpg")

session.add(lens4)
session.commit()


lens5 = Lens(
       user_id=1,
       name="Olympus M. 40-150mm F4.0-5.6 R Zoom Lens (Black) for Olympus" +
            " and Panasonic Micro 4/3 Cameras",
       brand="Olympus",
       style="Zoom",
       zoom_min="40",
       zoom_max="150",
       aperture="4.5-5.6",
       price_per_day="33.00",
       price_per_week="210.00",
       price_per_month="480.00",
       picture="5/olympus.jpg")

session.add(lens5)
session.commit()


lens6 = Lens(
       user_id=1,
       name="Sigma 17-50mm f/2.8 EX DC OS HSM FLD Large Aperture Standard" +
            " Zoom Lens for Canon Digital DSLR Camera",
       brand="Canon",
       style="Zoom",
       zoom_min="17",
       zoom_max="50",
       aperture="2.8",
       price_per_day="10.00",
       price_per_week="23.00",
       price_per_month="50.00",
       picture="6/1.jpg")

session.add(lens6)
session.commit()


lens7 = Lens(
       user_id=1,
       name="Sony SEL90M28G FE 90mm f/2.8-22 Macro G OSS Standard-Prime " +
            "Lens for Mirrorless Cameras",
       brand="Sony",
       style="Macro",
       zoom_min="90",
       zoom_max="90",
       aperture="2.8",
       price_per_day="8.00",
       price_per_week="18.00",
       price_per_month="40.00",
       picture="7/1.jpg")

session.add(lens7)
session.commit()


lens8 = Lens(
       user_id=1,
       name="Rokinon TSL24M-P 24mm f/3.5 Tilt Shift Lens for Pentax KAF " +
            "Cameras",
       brand="Pentax",
       style="Tilt-Shift",
       zoom_min="24",
       zoom_max="24",
       aperture="3.5",
       price_per_day="5.00",
       price_per_week="15.00",
       price_per_month="35.00",
       picture="8/1.jpg")

session.add(lens8)
session.commit()


lens9 = Lens(
       user_id=1,
       name="PENTAX DA 10-17mm f/3.5-4.5 ED (IF) Fish-Eye Lens for Pentax " +
            "Digital SLR",
       brand="Pentax",
       style="Fisheye",
       zoom_min="10",
       zoom_max="30",
       aperture="4",
       price_per_day="3.00",
       price_per_week="12.00",
       price_per_month="28.00",
       picture="9/1.jpg")

session.add(lens9)
session.commit()


lens10 = Lens(
       user_id=1,
       name="Fujinon XF 23mm F1.4 R",
       brand="Fujifilm",
       style="Prime",
       zoom_min="23",
       zoom_max="23",
       aperture="1.4",
       price_per_day="18.00",
       price_per_week="28.00",
       price_per_month="50.00",
       picture="10/1.jpg")

session.add(lens10)
session.commit()


lens11 = Lens(
       user_id=1,
       name="Nikon AF-S FX NIKKOR 24-70mm f/2.8G ED Zoom Lens with Auto " +
            "Focus for Nikon DSLR Cameras",
       brand="Nikon",
       style="Zoom",
       zoom_min="24",
       zoom_max="70",
       aperture="2.8",
       price_per_day="35.00",
       price_per_week="80.00",
       price_per_month="350.00",
       picture="11/1.jpg")

session.add(lens11)
session.commit()


lens12 = Lens(
       user_id=1,
       name="Rokinon 14mm f/2.8 IF ED UMC Ultra Wide Angle Fixed Lens w/" +
            " Built-in AE Chip for Nikon",
       brand="Nikon",
       style="Wide Angle",
       zoom_min="14",
       zoom_max="14",
       aperture="2.8",
       price_per_day="10.00",
       price_per_week="24.00",
       price_per_month="60.00",
       picture="12/1.jpg")

session.add(lens12)
session.commit()


lens13 = Lens(
       user_id=1,
       name="Panasonic H-HS35100 35-100mm Lens for G-Series Lumix Cameras",
       brand="Lumix",
       style="Zoom",
       zoom_min="35",
       zoom_max="35",
       aperture="2.8",
       price_per_day="10.00",
       price_per_week="24.00",
       price_per_month="60.00",
       picture="13/1.jpg")

session.add(lens13)
session.commit()


lens14 = Lens(
       user_id=1,
       name="Olympus M.ZUIKO Digital ED 45mm F1.8 (Black) Lens for Olympus" +
            " and Panasonic Micro 4/3 Cameras",
       brand="Olympus",
       style="Prime",
       zoom_min="45",
       zoom_max="45",
       aperture="1.8",
       price_per_day="10.00",
       price_per_week="24.00",
       price_per_month="60.00",
       picture="14/1.jpg")

session.add(lens14)
session.commit()


lens15 = Lens(
       user_id=1,
       name="Sony 24-70mm F4 Vario-Tessar T* FE OSS Interchangeable Full" +
            " Frame Zoom Lens",
       brand="Sony",
       style="Zoom",
       zoom_min="24",
       zoom_max="70",
       aperture="2.8",
       price_per_day="23.00",
       price_per_week="55.00",
       price_per_month="280.00",
       picture="15/1.jpg")

session.add(lens15)
session.commit()


rental1 = Rental(
       start_date=datetime.date(2016, 2, 12),
       end_date=datetime.date(2016, 2, 15),
       renter_id=2,
       owner_id=1,
       lens_id=11)

session.add(rental1)
session.commit()


rental2 = Rental(
       start_date=datetime.date(2016, 1, 24),
       end_date=datetime.date(2016, 6, 18),
       renter_id=2,
       owner_id=1,
       lens_id=3)

session.add(rental2)
session.commit()


rental3 = Rental(
       start_date=datetime.date(2016, 1, 01),
       end_date=datetime.date(2017, 2, 18),
       renter_id=2,
       owner_id=1,
       lens_id=8)

session.add(rental3)
session.commit()


print "added lenses!"
