"""Script to generate the database structure"""
from bs4 import BeautifulSoup
from database import Base, engine, db_session
from models import *

Base.metadata.create_all(bind=engine)

with open("items_list.html", "r") as f:
    soup = BeautifulSoup(f.read(), "html.parser")
    for item in soup.find_all("tr"):
        id_, img, name = item.find_all("td")
        db_session.add(ItemName(id_.string, name.a.string))
    db_session.commit()
