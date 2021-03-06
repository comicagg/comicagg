import os
import signal
import sys

def is_running():
    path = os.path.join('/tmp', os.path.basename(sys.argv[0]) + ".pid")
    if os.path.exists(path):
        try:
            pid = int(open(path).read())
            print("Already running on pid " + pid)
            os.kill(pid, signal.SIGTERM)
            print("Killed pid" + pid)
        except:
            print("Didn't kill anything")
    else:
        print("Not already running")
    f = open(path, 'w')
    f.write(str(os.getpid()))
    f.close()

def not_running_anymore():
    path = os.path.join('/tmp', os.path.basename(sys.argv[0]) + ".pid")
    if os.path.exists(path):
        os.remove(path)
        print("Deleted pid file")
    else:
        print("No pid file to delete")
