from select import select
import time
import random

from McClient.Events import EventManager
from McClient.networking import Connection, Receiver, Sender, OfflineSession, Session, ConnectionClosed

PLAYER_NAMES = [
    "Alice",
    "Bernard",
    "Charlie",
    "Danika",
    "Evan",
    "Fara",
    "Gunther",
    "Hagar",
    "Iain",
    "Juniper",
    "Kelsey",
    "Lamar",
    "Monique",
    "Norbert",
    "Olivia",
    "Penelope",
    "Quinn",
    "Rutiger",
]

class StandinClient(Connection):
    host = None
    port = None
    username = None
    password = None

    has_position = False
    position_queue = []

    x = None
    y = None
    z = None
    stance = None
    yaw = None
    pitch = None
    on_ground = None

    def __init__(self):
        super(StandinClient, self).__init__(None, EventManager, Receiver, Sender)
        self.eventmanager.apply(self)
        # self.eventmanager.got_event.add_handler(self.on_event)

    def on_event(self, *args, **kwargs):
        print "{0}: {1} {2}".format(self.username, args, kwargs)

    def login(self, host, port, username, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.reconnect()

    def reconnect(self):
        print "{0} logging in".format(self.username)
        if not self.password:
            session = OfflineSession()
        else:
            session = Session()
        session.connect(self.username, self.password)
        self.session = session

        super(StandinClient, self).connect(self.host, self.port)

    def recv_client_disconnect(self, reason):
        print "{0} was kicked: {1}".format(self.username, reason)
        self.has_position = False
        # self.login(self.host, self.port, self.username, self.password)

    def recv_player_position_and_look(self, x, y, stance, z, yaw, pitch, on_ground):
        self.x = x
        self.y = y
        self.stance = stance
        self.z = z
        self.yaw = yaw
        self.pitch = pitch
        self.on_ground = on_ground
        self.has_position = True

        print "{7} updated from server: pos=({0},{1},{2}) yaw={3} pitch={4} stance={5} on_ground={6}".format(
            self.x, self.y, self.z, self.yaw, self.pitch, self.stance, self.on_ground, self.username)

        self.update_server()

    def update_server(self):
        if self.has_position:
            # print "Updating server"
            self.stance = self.y + 1.0
            self.sender.send_player_position_and_look(self.x, self.y, self.stance, self.z, self.yaw, self.pitch, self.on_ground)

    def recv_update_health(self, health, food, saturation):
        print "{3} updated from server: health={0} food={1} saturation={2}".format(health, food, saturation, self.username)

        if health <= 0:
            self.respawn()

    def respawn(self):
        print "{0} respawning".format(self.username)
        self.sender.send_client_status(1)

    def idle_motion(self):
        if self.has_position and random.random() < 0.05:
            self.pitch = random.random() * 30.0 - 15.0
            self.yaw += random.random() * 60.0 - 30.0
            if self.yaw < 0.0:
                self.yaw += 360.0
            elif self.yaw > 360.0:
                self.yaw -= 360.0

    def wait_for_data(self, timeout=None):
        return len(select([self.socket.socket], [], [], timeout)[0]) > 0

    def loop(self):
        next_update = time.clock()+ 0.05

        while not self.killed:
            try:
                now = time.clock()
                if next_update > now:
                    if self.socket.wait4data(next_update - now):
                        self.receiver.data_received()
                else:
                    self.idle_motion()
                    self.update_server()
                    next_update = time.clock() + 0.05
            except ConnectionClosed as ex:
                print "ConnectionClosed: {0}".format(ex.message)
                return
                # self.reconnect()

clients = []
for i in xrange(1): # <--- number of bots
    client = StandinClient()
    client.login("192.168.2.11", 25565, PLAYER_NAMES[i])
    clients.append(client)
    time.sleep(5)

for client in clients:
    client.join()