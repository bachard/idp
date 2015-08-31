"""
Server based on Flask to handle player connections, manage players and visualize data, inspired by the RESTFul model

For interaction with clients, a json is sent back containing:
    * status: integer, -1 for server error, 0 for error, 1 for correct response
    * text: string, message displayed to the client
    * data: json/text, optional

In a first step, a client identifies himself with a player key, and gets his player id ("identification" function).
In a second step, the client makes himself available for connection ("connect" function).

"""

from flask import Flask
from flask import request, render_template, redirect, url_for, flash, make_response
from flask import json, jsonify

import sqlite3
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy import func, desc

import re
import time
from random import randint
from threading import Thread, Lock

# for py2exe to correctly import jinja2
import jinja2.ext

from database import db_session
from models import Session, Test, Stat, Item, Connection, Player
import utils

# We load the general settings
settings = utils.read_settings()

app = Flask(__name__)
app.secret_key = settings["flask"]["secret_key"]
app.debug = settings["flask"]["debug"]
app.ext = settings["flask"]["ext"]

# Lock used in the identification phase
app.lock_players = Lock()
# Lock used in the connection phase
app.lock_connections = Lock()



#########################################
# Players identification and connection #
#########################################



@app.route("/identification/", methods=["POST"])
def indentification():
    """
    Checks the validity of a key sent by a client in the POST arguments
    Returns the player id if the identification is successful
    """
    # We first check if the required field is sent
    if "key" in request.form:
        key = request.form["key"]
        print("    [ {} waiting for the players lock... ]".format(key))
        # We wait for the connection lock
        # This lock is used to ensure that no 2 client can connect with the same key
        app.lock_connections.acquire()
        print("    [ {} has acquired the players lock... ]".format(key))
        # We check if the key exists and is not already used
        try:
            player = db_session.query(Player).filter_by(key=key).one()
            if player.in_use == 0:
                # The key is now used
                player.in_use = 1
                db_session.commit()
                return jsonify(status=1, data={"player_id": player.id}, text="Identification successful...")
            else:
                # The key is already used
                return jsonify(status=-1, data={"player_id": player.id}, text="Key already in use!\nPlease enter another key...")
            
        except NoResultFound as e:
            return jsonify(status=0, text="You entered a wrong key! Try again...")
        except Exception as e:
            print(e)
            return jsonify(status=-1, text="Server error, try again please."), 500
        finally:
            # Once the database interaction is over, we release the connection lock
            print("    [ {} has released the connections lock ]".format(key))
            app.lock_connections.release()
    else:
        # The required field was not sent
        key = None
        return jsonify(status=0, text="Wrong request!"), 400


    

@app.route("/connect/", methods=["POST"])
def connect():
    """
    A client makes himself available for connetion giving his player id in the POST request
    If he is successfuly added to available players, the connection id is returned and  a thread is launched to find another available player
    """
    player_id = int(request.form["id"])
    print("    [ {} waiting for the connections lock... ]".format(player_id))
    # We wait for the connection lock
    # The lock is used for integrity, to ensure the connection by pair
    app.lock_connections.acquire()
    print("    [ {} has acquired the connections lock... ]".format(player_id))
    try:
        # We add the player to the players available for connection
        player = Player.query.get(player_id)
        conn = Connection(player_id)
        conn_id = None
        print("Adding to db...")
        db_session.add(conn)
        db_session.commit()
        conn_id = conn.id
        print("Added to db...")
        # We launch a new thread to connect the player with another available player
        thread = Thread(target=connect_player, args=(player_id,), name="Connect-Player-{}".format(player_id))
        thread.start()
        return jsonify(status=1, data=conn_id, text="Added to available players...")
    except NoResultFound:
        # The player does not exists
        return jsonify(satus=0, data=None, text="This player does not exists!")
    except Exception as e:
        # Server error
        print(e)
        return jsonify(satus=-1, data=None, text="Server error...")
    finally:
        # Finally we release the connection lock
        app.lock_connections.release()
        print("    [ {} has released the connections lock ]".format(player_id))    
    


def connect_player(player_id):
    """
    For a specific player, looks for another available player and connects to him
    In this setting, only players with same session number and pair can be connected, but this can be removed
    """

    # We get the corresponding player
    try:
        player = Player.query.get(player_id)
    except:
        # if the player does not exist, we stop
        return 0
    
    connected = False
 
    while not connected:
        # We loop until we find an available player
        print("    [ {} waiting for connections the lock... ]".format(player_id))
        # We wait for the connection lock
        app.lock_connections.acquire()
        print("    [ {} has acquired the connections lock... ]".format(player_id))

        # We refresh the player values to see if it has been connected already
        player = Player.query.get(player_id)
        conn = player.connection
                
        if conn.connected_player_id is not None:
            # The player has already been connected
            connected = True
            app.lock_connections.release()
        else:
            # We look for the other player
            q = db_session.query(Connection).join(Connection.players).filter(Connection.player_id!=player_id, Connection.status==0, Player.session_nr==player.session_nr, Player.pair==player.pair)
            try:
                conn_with = q.first()
                # We connect the 2 players and assign the roles
                conn.status = 1
                conn.connected_player_id = conn_with.players.id
                conn.role = 0
                conn_with.status = 1
                conn_with.connected_player_id = conn.players.id
                conn_with.role = 1
                db_session.commit()
                connected = True
                print("Connected {} with {}".format(conn.player_id, conn_with.player_id))
            except Exception as e:
                # No player was found, we cancel any database modification
                db_session.rollback()
                print("No other player available... New attempt...")
            finally:
                # We release the lock
                app.lock_connections.release()

        print("    [ {} has released the connections lock ]".format(player_id))        
        if not connected:
            # We wait before attempting again
            time.sleep(1)
    
    return 0



@app.route("/connected_with/<string:player_id>", methods=["GET"])
def connected_with(player_id):
    """
    For a specific player, returns the connected player if it is connected
    """

    print("    [ {} waiting for connections the lock... ]".format(player_id))
    # We wait for the connection lock
    app.lock_connections.acquire()
    print("    [ {} has acquired the connections lock... ]".format(player_id))
    # We look if the player is connected and with whom
    try:
        player = Player.query.get(player_id)
        conn = player.connection
        
        if conn is None:
            # The player is not available for connection
            return jsonify(status=0, data=None, text="Player not available for connection!")
        if conn.connected_player_id is None:
            # The player has not been connected
            return jsonify(status=0, data=None, text="Not connected yet...")
        # We return as connection_id the connection id of the player with role 1 in the pair
        if conn.role == 1:
            connection_id = conn.id
        else:
            connection_id = conn.connected_player.connection.id
            
        return jsonify(status=1, data={"connection_id":connection_id, "connected_player_name": conn.connected_player.name, "connected_player_id": conn.connected_player.id, "role":conn.role}, text="OK")
    except NoResultFound as e:
        # The player does not exist
        return jsonify(status=0, data=None, text="This player does not exist!")
    except Exception as e:
        # Server error
        return jsonify(status=-1, data=None, text="Server error..."), 500
    finally:
        # Finally we release the lock
        app.lock_connections.release()
        print("    [ {} has released the connections lock ]".format(player_id))



@app.route("/disconnect/<string:player_id>", methods=["GET"])
def disconnect(player_id):
    """
    Disconnects a player and the connected player
    """
    
    print("    [ {} waiting for connections the lock... ]".format(player_id))
    # We wait for the connection lock
    app.lock_connections.acquire()
    print("    [ {} has acquired the connections lock... ]".format(player_id))
    # We look for the player and disconnect him and the connected player
    try:
        player = Player.query.get(player_id)
        conn = player.connection
        player.in_use = 0
        if conn is None:
            # The player is not connected
            return jsonify(status=1, data=None, text="Player not connected.")
        else:
            # We disconnect the player and the connected player
            db_session.delete(conn)
            if player.connection_other:
                connected_player_conn = player.connection_other
                connected_player_conn.connected_player_id = None
                connected_player_conn.role = None
                connected_player_conn.status = 0
            db_session.commit()
            return jsonify(status=1, data=None, text="Player disconnected.")
    except NoResultFound as e:
        # Either the player does not exist or it has already been disconnected
        return jsonify(status=0, data=None, text="Player not found in connections!\nEither it does not exists or it has already been disconnected.")
    except Exception as e:
        # Server error
        return jsonify(status=-1, data=None, text="Server error..."), 500
    finally:
        # Finally we realease the lock
        app.lock_connections.release()
        print("    [ {} has released the connections lock ]".format(player_id))



@app.route('/upload_json/', methods=['GET', 'POST'])
def upload_json():
    """
    Handles the JSON coming from Minecraft client containing statistics
    """
    if request.method == 'POST':
        # We get the JSON
        data = request.get_json(silent=True)
        if data:
            # We add the statistics to the database
            try:
                add_stats_to_db(data)
                return "Stats added to db.", 200
            except Exception as e:
                # Exception when adding statistics
                return "Problem adding stats to db: {}".format(e), 400
        else:
            # No JSON was sent
            return "No JSON data was sent!", 400
    else:
        return "Only POST requests are accepted.", 400



def add_stats_to_db(data):
    """Add data statistics to the database"""
    # Expected parameters
    session_uuid = data['session_id']
    world = data['world']
    round = data['round']
    player_id = data['player']
    stats = json.loads(data['stats'])
    position_over_time = data['position_over_time']
    try:
        solution = data['solution']
    except:
        solution = ""
    checkpoints = data['checkpoints']
    score = int(data['score'])
    
    # try to find if the session has already been created
    # if not: create a new one
    try:
        session = db_session.query(Session).filter_by(session_uuid=session_uuid).one()
        try:
            test = db_session.query(Test).filter_by(session_id=session.id, world=world, round=round).one()
        except:
            test = Test(session.id, world, round)
            session.tests.append(test)
        
    except:
        session = Session(session_uuid)
        test = Test(session.id, world, round)
        session.tests.append(test)
                       
    # try to find an existing stat for the player
    # if yes: update it
    # if not: create it
    try:
        stat = db_session.query(Stat).filter_by(test_id=test.id, player_id=player_id).one()
    except:
        stat = Stat(test.id, player_id)
        test.stats.append(stat)

    items = []

    try:
        stat.position_over_time = json.dumps(position_over_time)
    except Exception as e:
        print(e)

    stat.checkpoints = json.dumps(checkpoints)
    stat.solution = solution
    stat.score = score
    
    items = {}
    
    for (k,v) in stats.items():
        k = k.split('.')
        attr = k[0]
        if attr == 'stat':
            # changes columnName into column_name
            column = re.sub("([A-Z])","_\g<1>", k[1]).lower()
            if len(k) == 3:
                update = False
                item_id = k[2]
                # try to find an already existing item in db
                # if exists: update it
                # else: create it
                if not item_id in items:
                    items[item_id] = {}
                items[item_id][column] = v
            else:
                # only adds statistics defined in db
                try:
                    setattr(stat, column, v)
                except:
                    pass
        elif attr == 'achievement':
            achiev = k[1]
            if achiev == 'exploreAllBiomes':
                try:
                    setattr(stat, 'number_biomes', len(v['progress']))
                except:
                    pass
        else:
            pass

    for (item_id, item_values) in items.items():
        try:
            item = db_session.query(Item).filter_by(test_id=test.id, player_id=player_id, item_item=item_id).one()

        except:
            item = Item(test.id, player_id)
            test.items.append(item)
            setattr(item, 'item_item', item_id)

        for (action, n) in item_values.items():    
            setattr(item, action, n)

    db_session.add(session)
    db_session.commit()


    
#########################################
# Web interface for managing statistics #
#########################################

# Templates are located in templates/ folder
# view_data.djhtml is the main templates for displaying generic data
# using columns and data arguments
# modifiable parameter specificies the columns that can be modified

@app.route('/')
def index():
    """By default, the user is redirected to the managing interface"""

    return redirect(url_for("view_index"))


    
@app.route("/view/")
def view_index():
    """Main interface for managing statistics and players"""

    return render_template("index.djhtml", title="Monitoring")



@app.route("/view/connections/")
def view_connections():
    """Shows the current connections"""

    columns = [c.name for c in Connection.__table__.columns]
    connections = db_session.query(Connection).all()
    return render_template("view_data.djhtml", title="Connections", columns=columns, data=connections)



@app.route("/view/sessions/")
def view_sessions():
    """Shows the saved sessions in the database"""

    columns = [c.name for c in Session.__table__.columns]
    # We add the link to the tests of the session
    columns.append("view_tests")
    sessions = db_session.query(Session).all()
    # For each tests in the session we get the corresponding id
    [setattr(session, "view_tests", "/view/tests/{}".format(session.id)) for session in sessions]
    
    return render_template("view_data.djhtml", title="Sessions", columns=columns, data=sessions)



@app.route("/view/tests/<int:session_id>")
def view_tests(session_id):
    """Show the tests of a specific session"""
    
    columns = [c.name for c in Test.__table__.columns]
    # We add the link to the stats and items of the test
    columns.append("view_stats")
    columns.append("view_items")
    tests = db_session.query(Test).filter_by(session_id=session_id).all()
    # For each stats and items in the test we get the corresponding id
    [setattr(test, "view_stats", "/view/stats/{}".format(test.id)) for test in tests]
    [setattr(test, "view_items", "/view/items/{}".format(test.id)) for test in tests]   

    return render_template("view_data.djhtml", title="Tests for session {}".format(session_id), columns=columns, data=tests, back="/view/sessions/")



@app.route("/view/stats/<int:test_id>")
def view_stats(test_id):
    """Show the stats for a specific test"""
    
    columns = [c.name for c in Stat.__table__.columns]
    # We remove columns we do not want to show
    columns.remove("position_over_time")
    stats = db_session.query(Stat).filter_by(test_id=test_id).all()
    # pretty print for the position_over_time field
    # for stat in stats:
    #     stat.position_over_time = {k: json.loads(v) for (k,v) in json.loads(stat.position_over_time).items()}

    # Link to go back to the tests
    session_id = db_session.query(Test).get(test_id).session_id

    return render_template("view_data.djhtml", title="Stats for test {}".format(test_id), columns=columns, data=stats, back="/view/tests/{}".format(session_id))



@app.route("/view/items/<int:test_id>")
def view_items(test_id):
    """Show the items for a specific test"""
    
    columns = [c.name for c in Item.__table__.columns]
    # We remove columns we do not want to show
    columns.remove("id")
    columns.remove("test_id")
    columns.remove("item_item")
    # We add the id and name of the item
    columns.insert(1, "item_id")
    columns.insert(2, "name")
    items = db_session.query(Item).filter_by(test_id=test_id).all()
    # We link the id and name of the item
    [setattr(item, "item_id", item.item.item) for item in items]
    [setattr(item, "name", item.item.name) for item in items]

    # Link to go back to the tests
    session_id = db_session.query(Test).get(test_id).session_id
    
    return render_template("view_data.djhtml", title="Items for test {}".format(test_id), columns=columns, data=items, back="/view/tests/{}".format(session_id))



##########################
# Export all data to CSV #
##########################

@app.route("/view/sessions/csv/")
def view_sessions_csv():
    """Exports the statistics data to a CSV file"""
    response = make_response(utils.stats_to_csv().getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=stats.csv"
    response.headers["Content-type"] = "text/csv"
    return response



######################
# Players management #
######################



@app.route("/players/")
def players():
    """Interface for managing players"""
    update_players_score()
    sessions = [s for s in db_session.query(Player.session_nr, func.count(Player.pair)).group_by(Player.session_nr).all()]
    return render_template("players.djhtml", title="Manage players", sessions=sessions)



def update_players_score():
    """Updates the score for each player"""
    for player in db_session.query(Player).all():
        try:
            last_test = db_session.query(Test).join(Stat).filter(Stat.player_id==player.id).order_by(desc(Test.timestamp)).one()
            score = 0
            team_score_avg = []
            team_score_max = 0
            for stat in last_test.stats:
                team_score_avg.append(stat.score)
                if stat.score > team_score_max:
                    team_score_max = stat.score
                if stat.player_id == player.id:
                    score = stat.score
            player.score = score
            player.team_score_avg = float(sum(team_score_avg)) / len(team_score_avg)
            player.team_score_max = team_score_max
            db_session.commit()            
        except Exception as e:
            print(e)


@app.route("/players/<int:session_nr>")
def view_players(session_nr):
    """
    Shows the players of a specific session
    Several fields can be modified
    """
    update_players_score()
    columns = [c.name for c in Player.__table__.columns]
    # Specificies the modifiable fields
    modifiable = ["name", "condition", "player_condition"]
    # Link to the target of the AJAX POST request for modifiying fields
    action = "/players/update/"
    players = db_session.query(Player).filter_by(session_nr=session_nr).all()
    return render_template("view_data.djhtml", title="Players for session {}".format(session_nr), id=session_nr, columns=columns, data=players, modifiable=modifiable, action=action, back="/players/")



@app.route("/players/create/", methods=["POST"])
def create_players():
    """Creates a session of number_players players"""
    if "number_players" in request.form:
        try:
            # We check if the parameter is an even int
            number_players = int(request.form["number_players"])
            if number_players % 2 != 0:
                flash("Odd number of players!")
            else:
                try:
                    # We compute the session number
                    last_session_nr = db_session.query(func.max(Player.session_nr)).one()[0]
                    last_session_nr = last_session_nr if last_session_nr else 0
                    session_nr = last_session_nr + 1
                    for i in range(number_players):
                        added = False
                        # For each player we generate a random key
                        while not added:
                            try:
                                key = '{0:06}'.format(randint(1, 1000000))
                                db_session.add(Player(key, key, session_nr, int(i/2) + 1, 0, i%2 + 1))
                                db_session.commit()
                                # The key did not exist and has been added
                                added = True
                            except Exception as e:
                                # The key already exists
                                db_session.rollback()
                    flash("The players were created! The session number is {}.".format(session_nr))
                except Exception as e:
                    # Unknown exception
                    flash("An exception has occured!<br />Exception message: {}".format(e))
                
        except ValueError as e:
            # The parameter was not an int
            flash("The argument is invalid! You did not pass an integer as parameter...")
    else:
        flash("Invalid form!")
    # Finally we redirect to the main interface
    return redirect(url_for("players"))



@app.route("/players/update/", methods=["POST"])
def update_player():
    """Updates players' information (AJAX call)"""
    data = request.get_json(silent=True)
    if data:
        try:
            for update_player in data["update_players"]:
                player_id = update_player.pop("id")
                player = db_session.query(Player).get(player_id)
                for (attr, value) in update_player.items():
                    setattr(player, attr, value)
                    db_session.add(player)
            db_session.commit()
            return jsonify(status=1, text="Update successful")
        except Exception as e:
            return jsonify(status=-1, data=str(e), text="Exception!")
    else:
        return jsonify(status=0, text="No JSON provided!")


    

@app.route("/players/export/csv/<int:session_number>", methods=["GET"])
def export_csv_players(session_number):
    """Exports the players as CSV"""
    try:
        response = make_response(utils.session_to_csv(session_number).getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=session_{}.csv".format(session_number)
        response.headers["Content-type"] = "text/csv"
        return response
    except Exception as e:
        # The session does not exist yet
        flash("Problem exporting the file! No players are available in the session.")
        return redirect(url_for("players"))



# Special file Allocation.txt needed for the intermediate game
# (Minecraft independent feature)
@app.route("/players/export/allocation/<int:session_number>", methods=["GET"])
def export_allocation_players(session_number):
    """Exports the Allocation.txt file"""
    try:
        response = make_response(utils.session_to_allocation_file(session_number).getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=Allocation.txt"
        response.headers["Content-type"] = "text/plain"
        return response
    except Exception as e:
        flash("Problem exporting the file! No players are available in the session.")
        return redirect(url_for("players"))



@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

    

if __name__ == '__main__':
    if not app.ext:
        app.run(port=1234, threaded=True)
    else:
        app.run(host='0.0.0.0', port=1234, threaded=True)
