from mcstatus import MinecraftServer
import a2s
import copy
import socket
from playhouse.shortcuts import model_to_dict
import urllib.request
import urllib.error

IP = "m311.ddns.net"


class Status:

    def __init__(self, service, compact):
        self.__service = service
        self.__compact = compact

        self.__service_mapper = {
            'Minecraft': self.__minecraft,
            'SRCDS': self.__srcds,
            'Web': self.__web
        }

    def get(self):
        res = self.__service_mapper[self.__service.service]()
        if self.__compact:
            return res

        res['db'] = model_to_dict(self.__service)

        return res

    def __minecraft(self):
        server = MinecraftServer(IP, self.__service.port)

        try:
            server.ping(retries=1)
        except socket.error:
            return {'online': False}

        if self.__compact:
            return {'online': True}

        try:
            res = server.status(retries=1)

            res_dict = copy.deepcopy(vars(res))
            res_dict['raw']['description'] = res_dict['raw']['description']['text']
            res_dict['raw']['ping'] = res_dict['latency']
            res_dict['raw']['online'] = True

            return res_dict['raw']

        except socket.error:
            return {'online': False}

    def __srcds(self):
        server = (IP, self.__service.port)

        try:
            info = a2s.info(server, timeout=0.3)
        except socket.timeout:
            return {'online': False}

        if self.__compact:
            return {'online': True}

        players = a2s.players(server, timeout=0.3)

        players_converted = []
        for player in players:
            player_dict = {}
            for attribute in dir(player):
                if attribute[0] != '_':
                    player_dict[attribute] = getattr(player, attribute)
            players_converted.append(player_dict)


        res_dict = {}
        res_dict['players'] = players_converted

        for attribute in dir(info):
            if attribute[0] != '_':
                res_dict[attribute] = getattr(info, attribute)

        res_dict['online'] = True

        return res_dict

    def __web(self):
        try:
            res = urllib.request.urlopen(f"http://{IP}:{self.__service.port}").getcode()
            if res == 200:
                return {'online': True}

            return {'online': False}
        except urllib.error.URLError:
            return {'online': False}
