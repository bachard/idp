"""
Client used for connecting to another player and launching Minecraft
The interface is using TkInter
Settings for the server and Minecraft are located in the settings.yml file
"""



import tkinter as tk
import time
import requests
from requests.exceptions import RequestException, ConnectionError
import subprocess
from utils import read_settings




class Application(tk.Frame):

    # settings is a common variable for all clients
    settings = read_settings()

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.player_id = None
        self.key = None
        self.master.title("Minecraft client")
        self.grid()
        self.createWidgets()
        self.server_root = "http://{}:{}/".format(self.settings["server"]["address"], self.settings["server"]["port"])

    def destroy(self):
        """Overrides the destroy method to disconnect the players first"""
        if self.player_id is not None:
            status = -1
            while status == -1:
                d = self.get_data("disconnect/{}".format(self.player_id))
                status = d["status"]
        tk.Frame.destroy(self)
        
    def createWidgets(self):
        """Creates the interface"""
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
        """Calls the identifcation method"""
        self.button_connect["state"] = tk.DISABLED
        self.field_connect["text"] = "Checking identification..."
        print(self.field_connect["text"])
        self.master.after(100, self.callback_identification)

    def callback_identification(self):
        """"Sends the key to the server for identification and calls the connection method"""
        self.key = self.var_key.get()
        d = self.get_data("identification/", method="POST", data={"key":self.key})

        if d["status"] == 1:
            # Identification went fine
            self.field_connect["text"] = d["text"]
            self.field_connect["text"] += "\nConnecting to server..."
            self.player_id = d["data"]["player_id"]
            self.conn_id = d["data"]["conn_id"]
            self.role = d["data"]["role"]
            print(self.player_id)
            print(self.field_connect["text"])
            self.master.after(100, self.callback_connection)
        else:
            # Identification problem
            self.field_connect["text"] = d["text"]
            self.button_connect["state"] = tk.NORMAL
            print(self.field_connect["text"])

    def callback_connection(self):
        """Sets the connection settings"""
        if self.role == 0:
            role = "Main"
        else:
            role = "Client"
        # Once the player is connected, we write the Minecraft connection files        
        with open(self.settings["minecraft"]["connection_file"], 'w') as f:
            f.write("{}\n{}\n".format(role, self.conn_id))

        with open(self.settings["minecraft"]["server_file"], 'w') as f:
            f.write("{}\n{}\n".format(self.server_root+"upload_json/", self.player_id))

        # Client is ready to launch the game
        self.field_connect["text"] = "Connected and ready to play!"
        print(self.field_connect["text"])
        self.button_connect["text"] = "Play!"
        self.button_connect["command"] = self.play
        self.button_connect["state"] = tk.NORMAL

    def get_data(self, url, method = "GET", data = None):
        """Generic method to reach the server"""
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
        """Updates the interface and calls the play callback"""
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



if __name__ == '__main__':
    # We launch the interface    
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
