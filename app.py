import sqlite3
from flask import Flask, request, render_template, redirect, url_for, flash, make_response
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy import func
from database import db_session
from models import Session, Test, Stat, Item, Connection, Player
from flask import json, jsonify
import re
import time
from random import randint
from threading import Thread, Lock
import utils

app = Flask(__name__)
app.secret_key = 'some_secret'

app.debug = True

app.ext = False

app.lock_connections = Lock()
app.lock_players = Lock()

@app.route('/', methods=["GET"])
def index():
    return redirect(url_for("view_index"))

@app.route("/identification/", methods=["POST"])
def indentification():
    if "key" in request.form:
        key = request.form["key"]
        print(key)
        print("    [ {} waiting for the players lock... ]".format(key))
        app.lock_connections.acquire()
        print("    [ {} has acquired the players lock... ]".format(key))
        try:
            player = db_session.query(Player).filter_by(key=key).one()
            if player.in_use == 0:
                player.in_use = 1
                db_session.commit()
                return jsonify(status=1, data={"player_id": player.id}, text="Identification successful...")
            else:
                return jsonify(status=-1, data={"player_id": player.id}, text="Key already in use!\nPlease enter another key...")
            
        except NoResultFound as e:
            return jsonify(status=0, text="You entered a wrong key! Try again...")
        except Exception as e:
            print(e)
            return jsonify(status=-1, text="Server error, try again please."), 500
        finally:
            print("    [ {} has released the connections lock ]".format(key))
            app.lock_connections.release()
            
    else:
        key = None
        return jsonify(status=0, text="Wrong request!"), 400


    

@app.route("/connect/", methods=["POST"])
def connect():
    # TODO: handle disconnection case/script crash and
    # player has already been connected but try to reconnect
    start = time.time()
    player_id = int(request.form["id"])
    print("    [ {} waiting for the connections lock... ]".format(player_id))
    app.lock_connections.acquire()
    print("    [ {} has acquired the connections lock... ]".format(player_id))
    try:
        player = Player.query.get(player_id)
        conn = Connection(player_id)
        conn_id = None
        print("Adding to db...")
        db_session.add(conn)
        db_session.commit()
        conn_id = conn.id
        print("Added to db...")
        end = time.time()
        thread = Thread(target=connect_player, args=(player_id,), name="Connect-Player-{}".format(player_id))
        thread.start()
        return jsonify(status=1, data=conn_id, text="Added to available players...")
    except NoResultFound:
        return jsonify(satus=0, data=None, text="This player does not exists!")
    except Exception as e:
        print(e)
        return jsonify(satus=-1, data=None, text="Server error...")
    finally:
        app.lock_connections.release()
        print("    [ {} has released the connections lock ]".format(player_id))    
    

def connect_player(player_id):
    start = time.time()

    try:
        player = Player.query.get(player_id)
    except:
        return 0
    
    connected = False
 
    while not connected:
        print("    [ {} waiting for connections the lock... ]".format(player_id))
        app.lock_connections.acquire()
        print("    [ {} has acquired the connections lock... ]".format(player_id))

        player = Player.query.get(player_id)
        print(player)
        conn = player.connection
        print(player.connection)
        
        if conn.connected_player_id is not None:
            connected = True
            app.lock_connections.release()
        else:
            q = db_session.query(Connection).join(Connection.players).filter(Connection.player_id!=player_id, Connection.status==0, Player.session_nr==player.session_nr, Player.pair==player.pair)
            try:
                conn_with = q.first()
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
                db_session.rollback()
                print(e)
                print("No other player available... New attempt...")
            finally:
                app.lock_connections.release()

        print("    [ {} has released the connections lock ]".format(player_id))        
        if not connected:
            time.sleep(1)

    end = time.time()    
    return 0


@app.route("/connected_with/<string:player_id>", methods=["GET"])
def connected_with(player_id):
    print("    [ {} waiting for connections the lock... ]".format(player_id))
    app.lock_connections.acquire()
    print("    [ {} has acquired the connections lock... ]".format(player_id))
    try:
        player = Player.query.get(player_id)
        conn = player.connection
        
        if conn is None:
            return jsonify(status=0, data=None, text="Player not available for connection!")
        if conn.connected_player_id is None:
            return jsonify(status=0, data=None, text="Not connected yet...")
        if conn.role == 1:
            connection_id = conn.id
        else:
            connection_id = conn.connected_player.connection.id
            
        return jsonify(status=1, data={"connection_id":connection_id, "connected_player_name": conn.connected_player.name, "connected_player_id": conn.connected_player.id, "role":conn.role}, text="OK")
    except NoResultFound as e:
        print(e)
        return jsonify(status=0, data=None, text="This player does not exist!")
    except Exception as e:
        print(e)
        return jsonify(status=-1, data=None, text="Server error..."), 500
    finally:
        app.lock_connections.release()
        print("    [ {} has released the connections lock ]".format(player_id))



@app.route("/disconnect/<string:player_id>", methods=["GET"])
def disconnect(player_id):
    print("    [ {} waiting for connections the lock... ]".format(player_id))
    app.lock_connections.acquire()
    print("    [ {} has acquired the connections lock... ]".format(player_id))
    try:
        player = Player.query.get(player_id)
        conn = player.connection
        player.in_use = 0
        if conn is None:
            return jsonify(status=1, data=None, text="Player not connected.")
        else:
            db_session.delete(conn)
            if player.connection_other:
                connected_player_conn = player.connection_other
                connected_player_conn.connected_player_id = None
                connected_player_conn.role = None
                connected_player_conn.status = 0
            db_session.commit()
            return jsonify(status=1, data=None, text="Player disconnected.")
    except NoResultFound as e:
        print(e)
        return jsonify(status=0, data=None, text="Player not found in connections!\nEither it does not exists or it has already been disconnected.")
    except Exception as e:
        print(e)
        return jsonify(status=-1, data=None, text="Server error..."), 500
    finally:
        app.lock_connections.release()
        print("    [ {} has released the connections lock ]".format(player_id))



@app.route('/upload_json/', methods=['GET', 'POST'])
def upload_json():
    if request.method == 'POST':
        #TODO:
        # check if JSON
        data = request.get_json(silent=True)
        if data:
            print(data)
            try:
                add_stats_to_db(data)
                return "Stats added to db.", 200
            except Exception as e:
                print(e)
                return "Problem adding stats to db: {}".format(e), 400
            
        else:
            print("No JSON")
            return "No JSON data was sent!", 400
    else:
        return "Only POST requests are accepted.", 400

    
@app.route("/view/")
def view_index():
    return render_template("index.djhtml", title="Monitoring")



@app.route("/view/connections/")
def view_connections():
    columns = [c.name for c in Connection.__table__.columns]
    connections = db_session.query(Connection).all()
    return render_template("view_data.djhtml", title="Connections", columns=columns, data=connections)



@app.route("/view/sessions/")
def view_sessions():
    columns = [c.name for c in Session.__table__.columns]
    columns.append("view_tests")
    sessions = db_session.query(Session).all()
    [setattr(session, "view_tests", "/view/tests/{}".format(session.id)) for session in sessions]
    
    return render_template("view_data.djhtml", title="Sessions", columns=columns, data=sessions)



@app.route("/view/tests/<int:session_id>")
def view_tests(session_id):
    columns = [c.name for c in Test.__table__.columns]
    columns.append("view_stats")
    columns.append("view_items")
    tests = db_session.query(Test).filter_by(session_id=session_id).all()
    [setattr(test, "view_stats", "/view/stats/{}".format(test.id)) for test in tests]
    [setattr(test, "view_items", "/view/items/{}".format(test.id)) for test in tests]   
    return render_template("view_data.djhtml", title="Tests for session {}".format(session_id), columns=columns, data=tests, back="/view/sessions/")


@app.route("/view/stats/<int:test_id>")
def view_stats(test_id):
    columns = [c.name for c in Stat.__table__.columns]
    stats = db_session.query(Stat).filter_by(test_id=test_id).all()
    for stat in stats:
        stat.position_over_time = {k: json.loads(v) for (k,v) in json.loads(stat.position_over_time).items()}
    session_id = db_session.query(Test).get(test_id).session_id
    return render_template("view_data.djhtml", title="Stats for test {}".format(test_id), columns=columns, data=stats, back="/view/tests/{}".format(session_id))


@app.route("/view/items/<int:test_id>")
def view_items(test_id):
    columns = [c.name for c in Item.__table__.columns]
    items = db_session.query(Item).filter_by(test_id=test_id).all()
    session_id = db_session.query(Test).get(test_id).session_id
    return render_template("view_data.djhtml", title="Items for test {}".format(test_id), columns=columns, data=items, back="/view/tests/{}".format(session_id))




@app.route("/view/sessions/csv/")
def view_sessions_csv():
    response = make_response(utils.stats_to_csv().getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=stats.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route("/keys/")
def keys():
    sessions = [s for s in db_session.query(Player.session_nr, func.count(Player.pair)).group_by(Player.session_nr).all()]
    return render_template("keys.djhtml", title="Manage keys", sessions=sessions)

@app.route("/keys/<int:session_nr>")
def view_keys(session_nr):
    columns = [c.name for c in Player.__table__.columns]
    players = db_session.query(Player).filter_by(session_nr=session_nr).all()
    return render_template("view_data.djhtml", title="Keys for session {}".format(session_nr), columns=columns, data=players, back="/keys/")

@app.route("/keys/create/", methods=["POST"])
def create_keys():
    if "number_players" in request.form:
        try:
            number_players = int(request.form["number_players"])
            if number_players % 2 != 0:
                flash("Even number of players!")
            else:
                try:
                    last_session_nr = db_session.query(func.max(Player.session_nr)).one()[0]
                    last_session_nr = last_session_nr if last_session_nr else 0
                    session_nr = last_session_nr + 1
                    for i in range(number_players):
                        added = False
                        while not added:
                            try:
                                key = '{0:06}'.format(randint(1, 1000000))
                                db_session.add(Player(key, key, session_nr, int(i/2)))
                                db_session.commit()
                                added = True
                            except Exception as e:
                                db_session.rollback()
                    flash("The keys were created! The session number is {}.".format(session_nr))
                except Exception as e:
                    flash("An exception has occured!<br />Exception message: {}".format(e))
                
        except ValueError as e:
            flash("The argument is invalid! You did not pass an integer as parameter...")
    else:
        flash("Invalid form!")
    return redirect(url_for("keys"))

@app.route("/keys/print/<int:session_number>", methods=["GET"])
def print_keys(session_number):
    try:
        response = make_response(utils.session_to_csv(session_number).getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=session_{}.csv".format(session_number)
        response.headers["Content-type"] = "text/csv"
        return response
    except Exception as e:
        flash("Problem printing the file! No players are available in the session.")
        return redirect(url_for("keys"))


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
    

def add_stats_to_db(data):
    session_uuid = data['session_id']
    world = data['world']
    round = data['round']
    player_id = data['player']
    stats = json.loads(data['stats'])
    position_over_time = data['position_over_time']
    checkpoints = data['checkpoints']
    
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

    stat.position_over_time = json.dumps(position_over_time)
    stat.checkpoints = json.dumps(checkpoints)
    
    print(test)
    print(stats)
        
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
                try:
                    item = db_session.query(Item).filter_by(test_id=test.id, player_id=player_id, item=item_id).one()
                except:
                    print(test)
                    item = Item(test.id, player_id)
                    test.items.append(item)
                    setattr(item, 'item', item_id)
                    
                setattr(item, column, v)
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

    db_session.add(session)
    # db_session.add(test)
    # db_session.add_all(items)
    db_session.commit()
    
if __name__ == '__main__':
    if not app.ext:
        app.run(port=1234, threaded=True)
    else:
        app.run(host='0.0.0.0', port=1234, threaded=True)
