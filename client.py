import tkinter as tk
import time
import requests
from requests.exceptions import RequestException, ConnectionError
import subprocess
from random import randint
from utils import read_settings

class Application(tk.Frame):

    settings = read_settings()

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.id_ = randint(0,1000)
        self.player_id = None
        self.key = None
        self.master.title("Player {}".format(self.id_))
        self.grid()
        self.createWidgets()
        self.server_root = "http://{}:{}/".format(self.settings["server"]["address"], self.settings["server"]["port"])
            
        
    def createWidgets(self):
        self.field_label = tk.Label(self, text="Enter your key:")
        self.var_key = tk.StringVar()
        self.input_key = tk.Entry(self, textvariable=self.var_key, width=30)
        self.button_connect = tk.Button(self, text="Connect", command=self.connect)
        self.field_connect = tk.Label(self, text=" ")
        
        self.field_label.grid(padx=10, pady=10)
        self.input_key.grid(padx=10, pady=10)
        self.button_connect.grid(padx=10, pady=10)
        self.field_connect.grid(padx=10, pady=10)
    
    def connect(self):
        self.button_connect["state"] = tk.DISABLED
        self.field_connect["text"] = "Checking identification..."
        print(self.field_connect["text"])
        self.master.after(100, self.callback_identification)

    def callback_identification(self):
        self.key = self.var_key.get()
        d = self.get_data("identification/", method="POST", data={"key":self.key})

        if d["status"] == 1:
            self.field_connect["text"] = d["text"]
            self.field_connect["text"] += "\nConnecting to server..."
            self.player_id = d["data"]["player_id"]
            print(self.player_id)
            print(self.field_connect["text"])
            self.master.after(100, self.callback_connection)
        else:
            self.field_connect["text"] = d["text"]
            self.button_connect["state"] = tk.NORMAL
            print(self.field_connect["text"])

    def callback_connection(self):
        d = self.get_data("connect/", method="POST", data={"id":self.player_id})

        if d["status"] == 1:
            self.field_connect["text"] = "Searching for other player..."
            self.master.after(100, self.callback_wait_for_connection)
        
    def callback_wait_for_connection(self):
        connected = False
        while not connected:
            d = self.get_data("connected_with/{}".format(self.player_id))
            if d["status"] == 1:
                connected = True
                d = d["data"]
            else:
                time.sleep(2)
                self.field_connect["text"] = d["text"]

        print(d)
        if d["role"] == 0:
            role = "Client"
        elif d["role"] == 1:
            role = "Main"
                
        with open(self.settings["minecraft"]["connection_file"], 'w') as f:
            f.write("{}\n{}\n".format(role, d["connection_id"]))

        with open(self.settings["minecraft"]["server_file"], 'w') as f:
            f.write("{}\n{}\n{}".format(self.server_root+"upload_json/", self.player_id, d["connected_player_id"]))

        self.field_connect["text"] = "Connected with {} as {}".format(d["connected_player_name"], role)
        print(self.field_connect["text"])
        self.button_connect["text"] = "Play!"
        self.button_connect["command"] = self.play
        self.button_connect["state"] = tk.NORMAL

    def get_data(self, url, method = "GET", data = None):
        url = self.server_root + url
        d = {}
        d["status"] = -1
        try:
            if method == "GET":
                r = requests.get(url)
                d = r.json()
            elif method == "POST":
                r = requests.post(url, data=data)
                d = r.json()
        except ConnectionError as e:
            d["text"] = "Server is not reachable.\n Please wait and try again..."
            
        except RequestException as e:
            d["text"] = "The server has encountered a problem.\n Please wait and try again..."

        except Exception as e:
            d["text"] = "An exception has occured!"

        finally:
            return d
        
    def play(self):
        self.field_label["text"] = "Good game!"
        self.button_connect["text"] = "Playing..."
        self.button_connect["command"] = None
        self.button_connect["state"] = tk.DISABLED
        self.field_connect["text"] = "Please wait for the launcher to start.\n Then click 'Play' to start playing!"
        self.master.after(100, self.callback_play)
        

    def callback_play(self):
        ret = subprocess.call([self.settings["java"]["path"], "-jar", self.settings["minecraft"]["path"]])
        if ret == 0:
            self.field_label["text"] = "You exited the game.\n Click play if you want to continue playing.\n You can close the client if you have finished playing."
        else:
            self.field_label["text"] = "There was an error and the game has closed.\nClick play if you want to continue playing.\n You can close the client if you have finished playing."
        self.button_connect["text"] = "Play!"
        self.button_connect["command"] = self.play
        self.button_connect["state"] = tk.NORMAL
        self.field_connect["text"] = ""
        
        
    
root = tk.Tk()
app = Application(master=root)
app.mainloop()
