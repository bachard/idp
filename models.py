"""
Models for SQLAlchemy ORM
Please see http://docs.sqlalchemy.org/en/rel_1_0/orm/tutorial.html for more details on SQLAlchemy
"""

from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, Text
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from datetime import datetime
from database import Base


class Session(Base):
    """Base model for all sessions stored in DB"""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    session_uuid = Column(String(40)) # UUID of the session (sent by Minecraft client) 
    timestamp = Column(DateTime) # Creation timestamp of the session

    # Reference to the tests of the session
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
    """Base model for all tests stored in DB"""
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id")) # ID of the session
    world = Column(String(40)) # Name of the world
    round = Column(String(40)) # Round number in the world
    timestamp = Column(DateTime) # Creation timestamp of the test

    # Reference to the stats of the test
    stats = relationship("Stat", order_by="Stat.player_id", backref="test", cascade="all, delete, delete-orphan")
    # Reference to the items of the test
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
    """Base model for all stats stored in DB"""
    __tablename__ = "stats"
    
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey("tests.id")) # ID of the test
    player_id = Column(Integer, ForeignKey("players.id")) # ID of the player

    checkpoints = Column(Text) # Checkpoints the player activated, generated by the Minecraft mod
    position_over_time = Column(Text) # Position over time of the player, generated by the Minecraft mod
    solution = Column(String(100)) # Solution chosen by the player, generated by the Minecraft mod

    score = Column(Integer, default=0) # Score earned by the player on the round
    
    # Minecraft generated statistics
    play_one_minute = Column(Integer, default=0)
    walk_one_cm = Column(Integer, default=0)
    swim_one_cm = Column(Integer, default=0)
    dive_one_cm = Column(Integer, default=0)
    jump = Column(Integer, default=0)
    
    climb_one_cm = Column(Integer, default=0)
    fly_one_cm = Column(Integer, default=0)
    boat_one_cm = Column(Integer, default=0)
    minecart_one_cm = Column(Integer, default=0)
    pig_one_cm = Column(Integer, default=0)
    horse_one_cm = Column(Integer, default=0)

    fall_one_cm = Column(Integer, default=0)
    damage_taken = Column(Integer, default=0)
    deaths = Column(Integer, default=0)

    damage_dealt = Column(Integer, default=0)
    mob_kills = Column(Integer, default=0)
    player_kills = Column(Integer, default=0)

    drop = Column(Integer, default=0)
    number_biomes = Column(Integer, default=0)

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
    """Base model for all items stored in DB"""
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey("tests.id")) # ID of the test
    player_id = Column(Integer, ForeignKey("players.id")) # ID of the player
    # Reference to the item from ItemNames table
    item_item = Column(String(40), ForeignKey("item_names.item")) 
    item = relationship("ItemName")
    # Minecraft generated statistics
    use_item = Column(Integer, default=0)
    mine_block = Column(Integer, default=0)
    craft_item = Column(Integer, default=0)
    break_item = Column(Integer, default=0)

    def __init__(self, test_id, player_id):
        self.test_id = test_id
        self.player_id = player_id
    
    def __repr__(self):
        s = "Item #{} ({}): used {}, mined {}, crafted {}, broken {}".format(self.item_item, self.item.name, self.use_item, self.mine_block, self.craft_item, self.break_item)
        return s
    

class Connection(Base):
    """Base model for all connections stored in DB"""
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, unique=True) # ID of the player
    connected_player_id = Column(Integer, ForeignKey("players.id"), nullable=True) # ID of the connected player
    status = Column(Integer) # status of the connection
    role = Column(Integer) # role of the player in the connection (0 or 1)
    
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
    """Base model for all players stored in DB"""
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    
    key = Column(String(100), unique=True) # Unique key of the player
    name = Column(String(40)) # name of the player
    in_use = Column(Boolean) # whether the player is active or not
    session_nr = Column(Integer) # number of the session
    pair = Column(Integer) # number of the pair
    condition = Column(Integer) # number of the condition
    player_condition = Column(Integer) # number of the player condition

    score = Column(Integer, default=0)
    team_score_avg = Column(Float, default=0.0)
    team_score_max = Column(Float, default=0.0)
    
    # Reference to the connection
    connection = relationship("Connection", foreign_keys=[Connection.player_id], backref="players", uselist=False, cascade="all, delete, delete-orphan")
    # Reference to the connected player connection
    connection_other = relationship("Connection", foreign_keys=[Connection.connected_player_id], uselist=False, cascade="all, delete, delete-orphan")

    def __init__(self, key, name, session_nr, pair, condition=0, player_condition=0):
        self.key = key
        self.name = name
        self.session_nr = session_nr
        self.pair = pair
        self.condition = condition
        self.player_condition = player_condition
        self.in_use = 0

        
    def __repr__(self):
        s = "key {}, name {}, used {}, session nr {}, pair {}, condition {}, player condition {}".format(self.key, self.name, self.in_use, self.session_nr, self.pair, self.condition, self.player_condition)
        return s


class ItemName(Base):
    """Contains the name of items by ID"""
    __tablename__ = "item_names"

    id = Column(Integer, primary_key=True)
    item = Column(String(40), unique=True) # Minecraft item ID
    name = Column(String(100)) # name of the item

    def __init__(self, item, name):
        self.item = item
        self.name = name

    def __repr__(self):
        return "{}, {}".format(self.item, self.name)
