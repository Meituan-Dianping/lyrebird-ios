import lyrebird
import pip
import threading


if __name__ == '__main__':
    pip.main(['install', '.',  '--upgrade'])
    lyrebird.run()
    threading.Event().wait()

