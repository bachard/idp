import subprocess
import os
from utils import read_settings

if __name__ == "__main__":
    print("Trying to read settings from settings.yml")
    try:
        settings = read_settings()
        print("Done!")
    except Exception as e:
        print("Something went wrong:{}".format(e))
    print("Trying to launch minecraft")
    try:
        ret = subprocess.call([settings["java"]["path"], "-jar", settings["minecraft"]["path"]])
        print("Done!")
    except Exception as e:
        print("Something went wrong:{}".format(e))
    print("Trying to write connection file")
    try:
        f = open(settings["minecraft"]["connection_file"], 'w')
        f.write("{}\n{}\n".format("TEST", "TEST"))  
        f.close()
        print("Done!")
    except Exception as e:
        print("Something went wrong:{}".format(e))
    os.system("pause")