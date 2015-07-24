from sqlalchemy import Column, Integer, String, Boolean, DateTime, LargeBinary
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from datetime import datetime
from hashlib import sha1
from database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    session_uuid = Column(String(40))
    timestamp = Column(DateTime)
    # mainclient = Column(Integer, ForeignKey("players.id"))
    # client = Column(Integer, ForeignKey("players.id"))

    tests = relationship("Test", order_by="Test.timestamp", backref="session", cascade="all, delete, delete-orphan")

    def __init__(self, session_uuid):
        self.session_uuid = session_uuid
        self.timestamp = datetime.now()
                    
    def __repr__(self):
        s = "[ id: {}, session_uuid: {}, timestamp: {} ]\n".format(self.id, self.session_uuid, self.timestamp)
        for test in self.tests:
            s += "    {}\n".format(test)
            
        return s


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    world = Column(String(40))
    round = Column(String(40))
    timestamp = Column(DateTime)

    stats = relationship("Stat", order_by="Stat.player_id", backref="test", cascade="all, delete, delete-orphan")
    items = relationship("Item", order_by="Item.player_id", backref="test", cascade="all, delete, delete-orphan")

    def __init__(self, session_id, world, round):
        self.session_id = session_id
        self.world = world
        self.round = round
        self.timestamp = datetime.now()

    
    def __repr__(self):
        s = "[ world: {}, round: {}, timestamp: {} ]\n".format(self.world, self.round, self.timestamp)

        for stat in self.stats:
            s += "        {}\n".format(stat)
            
        for item in self.items:
            s += "        {}\n".format(item)

        return s    
        
class Stat(Base):
    __tablename__ = "stats"
    
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey("tests.id"))
    player_id = Column(Integer, ForeignKey("players.id"))

    checkpoints = Column(LargeBinary)
    position_over_time = Column(LargeBinary)
    
    play_one_minute = Column(Integer)
    walk_one_cm = Column(Integer)
    swim_one_cm = Column(Integer)
    dive_one_cm = Column(Integer)
    jump = Column(Integer)
    
    climb_one_cm = Column(Integer)
    fly_one_cm = Column(Integer)
    boat_one_cm = Column(Integer)
    minecart_one_cm = Column(Integer)
    pig_one_cm = Column(Integer)
    horse_one_cm = Column(Integer)

    fall_one_cm = Column(Integer)
    damage_taken = Column(Integer)
    deaths = Column(Integer)

    damage_dealt = Column(Integer)
    mob_kills = Column(Integer)
    player_kills = Column(Integer)

    drop = Column(Integer)
    number_biomes = Column(Integer)

    def __init__(self, test_id, player_id):
        self.test_id = test_id
        self.player_id = player_id
        

    def __repr__(self):
        s = "[ player {} stats ]".format(self.player_id)
        for column in self.__table__.columns:
            name = column.name
            label = name.replace("_", " ")
            if getattr(self, name):
                s += "\n            [ {} : {} ]".format(label, getattr(self, name))
        return s
        
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey("tests.id"))
    player_id = Column(Integer, ForeignKey("players.id"))

    item = Column(Integer)
    use_item = Column(Integer)

    def __init__(self, test_id, player_id):
        self.test_id = test_id
        self.player_id = player_id
    
    def __repr__(self):
        s = "[ player {}, item {}: used {} times ]".format(self.player_id, self.item, self.use_item)
        return s
    

class Connection(Base):
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, unique=True)
    connected_player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    # session_nr = Column(Integer)
    # pair = Column(Integer)
    status = Column(Integer)
    role = Column(Integer)

    # player = relationship("Player", foreign_keys=[player_id], backref=backref("connections", uselist=False), single_parent=True, cascade="all, delete, delete-orphan")
    connected_player = relationship("Player", foreign_keys=[connected_player_id])
    
    def __init__(self, player_id):
        self.player_id = player_id 
        self.status = 0
        self.connected_player_id = None
        self.role = None
        
    
    def __repr__(self):
        s = "player {}, status {}, connected with {}".format(self.player_id, self.status, self.connected_player_id)
        return s
    
    def to_dict(self):
        return {
            "connected_player_id": self.connected_player_id,
            "role": self.role
        }
            
        
class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    
    key = Column(String(100), unique=True)
    name = Column(String(40))
    in_use = Column(Boolean)
    session_nr = Column(Integer)
    pair = Column(Integer)
    setup = Column(Integer)
    
    connection = relationship("Connection", foreign_keys=[Connection.player_id], backref="players", uselist=False, cascade="all, delete, delete-orphan")
    connection_other = relationship("Connection", foreign_keys=[Connection.connected_player_id], uselist=False, cascade="all, delete, delete-orphan")

    def __init__(self, key, name, session_nr, pair, setup=-1):
        self.key = key
        self.name = name
        self.session_nr = session_nr
        self.pair = pair
        self.setup = setup
        self.in_use = 0
    
    def __repr__(self):
        s = "key {}, name {}, used {}, session nr {}, pair {}".format(self.key, self.name, self.in_use, self.session_nr, self.pair)
        return s
