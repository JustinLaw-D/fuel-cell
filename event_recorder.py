from time import time
import keyboard

event_file = open('event_record.txt', 'a')
run = True

def handle_r(_kevent):
    event_file.write(str(time()) + '\n')

def handle_q(_kevent):
    global run
    run = False

def main():
    keyboard.on_press_key('r', handle_r)
    keyboard.on_press_key('q', handle_q) 

    while run:
        pass

    event_file.close()

main()
