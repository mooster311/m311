import datetime

from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from playhouse.shortcuts import model_to_dict

from apscheduler.schedulers.background import BackgroundScheduler
import atexit

from database import db, Service, HourlyData, DailyData
from status import Status

from tasks import check_statuses, check_ping, compile_hourly_data, compile_daily_data

scheduler = BackgroundScheduler()

scheduler.add_job(check_statuses, 'interval', minutes=1, id='statuses', misfire_grace_time=45)
scheduler.add_job(check_ping, 'interval', minutes=1, id='ping', misfire_grace_time=45)
scheduler.add_job(compile_hourly_data, 'interval', minutes=1, id='hourly', misfire_grace_time=360)
scheduler.add_job(compile_daily_data, 'interval', minutes=1, id='daily', misfire_grace_time=360)
scheduler.start()


app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})

@app.before_request
def before_request():
    db.connect()


@app.after_request
def after_request(response):
    db.close()
    return response


@app.route('/services')
def services():
    services = Service.select()

    res = []

    for service in services:
        return_dict = {
            'db': model_to_dict(service),
            'online': Status(service, True).get()['online']
        }

        res.append(return_dict)

    return jsonify(res)


@app.route('/services/<int:id>')
def service(id):
    service = Service.get_or_none(id=id)

    if service is None:
        return abort(404)

    if request.args.get('compact'):
        return_dict = {
            'db': model_to_dict(service),
            'online': Status(service, True).get()['online']
        }

        return return_dict

    return jsonify(Status(service, False).get())


@app.route('/metrics/<int:id>')
def metrics(id):
    service = Service.get_or_none(id=id)

    if service is None:
        return abort(404)

    data_type = request.args.get('timeframe')

    if data_type == 'hourly':

        data = HourlyData.select().where(HourlyData.service_id == service.id,
                                         HourlyData.created_at > datetime.datetime.now() - datetime.timedelta(
                                             hours=24)).dicts()

        return jsonify([r for r in data])


    elif data_type == 'daily':
        data = DailyData.select().where(DailyData.service_id == service.id,
                                        DailyData.created_at > datetime.datetime.now() - datetime.timedelta(
                                            days=30)).dicts()

        return jsonify([r for r in data])
    else:
        return abort(404)


atexit.register(lambda: scheduler.shutdown())


