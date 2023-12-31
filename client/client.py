import json
import pickle
import threading
import time
from socket import *
from threading import Thread

# Dictionary of help commands
_help_dict = {
    "help": "Display the help menu.",
    "set [number]": "Set the delay after each step in Hz.",
    "cw-step [number]": "Move clockwise in steps.",
    "ccw-step [number]": "Move counterclockwise in steps.",
    "cw-degrees [number]": "Move the motor clockwise by degrees.",
    "ccw-degrees [number]": "Move the motor counterclockwise by degrees.",
    "disconnect": "Disconnect from the server.",
    "shutdown": "Shutdown the application, client and server."
}


# This only works with the gpio version of the stepper_motor.py
class MyClient:
    def __init__(self):
        self.__SERVER_PORT = 50000  # Port for the server
        self.__BUFSIZE = 1024  # Set maximum bufsize

        self.host = input("Enter Server-IP Address: ").replace(" ", "")  # Set IP of host
        self.name = f"{gethostname()}:{self.__SERVER_PORT}"

        self.data_recv = None  # Storage for received messages
        self.data_send = None  # Storage for sent messages

        self.socket_connection = socket(AF_INET, SOCK_STREAM)  # Create IpV4-TCP/IP-socket
        self.socket_connection.connect((self.host, self.__SERVER_PORT))  # Connect to the server via IP and port

        print(f"Connected to Server: '{self.host}'.")

        self.exit = False  # Initiate boolean to end it all
        self.quit = False  # Initiate boolean to stop threads

        self.editJSON = False

        self.thread_send = Thread(target=self.worker_send)  # Setup thread for sending messages
        self.thread_send.start()  # Start thread to send messages

        self.lock = threading.Lock()  # Lock for the shutdown function

    # Function to send messages
    def worker_send(self):
        while not self.quit:
            try:
                print("Create your json-object. Type 'send' to send it.")
                self.editJSON = False
                # Setup data for the server which displays information about the client cpu frequency
                self.data_send = self.encode_json()  # Send a custom text message to server

                # Turn into bytes
                self.data_send = self.encode_pickle(self.data_send)

                # Send the server the data_send string
                self.socket_connection.send(self.data_send)

                # Sleep for a second
                time.sleep(1)
            except Exception as e:  # Catch error and print
                print(f"Error occurred in sending message: {e}")
        print("Stopped thread because self.quit is true.")

    # Function to turn a message into json
    def encode_json(self):
        json_object = {}
        while not self.editJSON:
            message = input("> ").lower()
            if message == "help":
                for help_entry, help_desc in _help_dict.items():
                    print(f"{help_entry}: {help_desc}")
            elif message == "send":
                print("JSON-Object will be sent to server.")
                self.editJSON = True
                break
            elif message == "disconnect":
                print("Going to send the object and then disconnect.")
                time.sleep(3)
                threading.Thread(self.stop_connection()).start()
                break
            elif message == "shutdown":
                print("Going to send the object and then shutdown.")
                time.sleep(3)
                threading.Thread(self.shutdown()).start()
                break
            else:
                function, amount = message.split(" ")
                json_object[function] = amount
        json_string = json.dumps(json_object)
        return json_string

    # Function to turn a message into pickle
    @staticmethod
    def encode_pickle(json_string):
        byte_message = pickle.dumps(json_string)
        return byte_message

    # Function to stop the connection - Doesn't close the application
    def stop_connection(self):
        self.quit = True  # Stop the while loop in worker_send
        time.sleep(1)
        self.thread_send.join()  # Stop thread for sending messages
        print("Stopped thread for sending messages.")
        time.sleep(1)
        self.socket_connection.close()  # Close socket
        print(f"Stopped connection for: {self.name}")
        time.sleep(1)
        print("Closing the application...")
        time.sleep(1)
        self.exit = True  # Stop the whole application
        exit(0)

    # Function to shut down the application
    def shutdown(self):
        with self.lock:
            print("Shutting down...")
            self.stop_connection()
