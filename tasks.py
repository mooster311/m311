import datetime

from database import db, Service, Logging, Ping, HourlyData, DailyData
from status import Status


def check_statuses():
    if db.is_closed():
        db.connect()

    services = Service.select()

    for service in services:
        online = Status(service, True).get()['online']
        Logging.create(online=online, service=service.id)

    db.close()


def check_ping():
    if db.is_closed():
        db.connect()

    services = Service.select()

    for service in services:
        if service.service != 'Web':
            try:
                ping = Status(service, False).get()['ping']
                Ping.create(ping=ping, service=service.id)
            except KeyError:
                pass

    db.close()


def compile_hourly_data():
    if db.is_closed():
        db.connect()

    services = Service.select()

    for service in services:

        if service.service != 'Web':
            pings = [ping.ping for ping in Ping.select().where(Ping.service_id == service.id,
                                                               Ping.created_at > datetime.datetime.now() - datetime.timedelta(
                                                                   hours=1))]

            is_offline = 0
            offlines = []

            for log in Logging.select().where(Logging.service_id == service.id,
                                              Logging.created_at > datetime.datetime.now() - datetime.timedelta(hours=1)):
                if not log.online:
                    if is_offline == 0:
                        offlines.append([log.created_at])
                        is_offline = 1
                elif log.online and is_offline == 1:
                    is_offline = 0
                    offlines[-1].append(log.created_at)

            total_time = 0
            for offline in offlines:
                total_time += (offline[1] - offline[0]).total_seconds()

            uptime = 100 - (total_time / 3600)

            if pings:
                ping = round((sum(pings) / len(pings)), 2)
            else:
                ping = None

            HourlyData.create(service=service.id, uptime=uptime, ping=ping)

    db.close()


def compile_daily_data():
    if db.is_closed():
        db.connect()

    services = Service.select()

    for service in services:
        if service.service != 'Web':
            hourly_data = [hourly for hourly in HourlyData.select().where(HourlyData.service_id == service.id,
                                                                          HourlyData.created_at > datetime.datetime.now() - datetime.timedelta(
                                                                              hours=24))]

            ping = 0
            uptime = 0

            for hourly in hourly_data:
                ping += hourly.ping
                uptime += hourly.uptime

            data_points = len(hourly_data)

            ping = ping / data_points
            uptime = uptime / data_points

            DailyData.create(service=service.id, uptime=uptime, ping=ping)

    db.close()

