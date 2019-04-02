#!/usr/bin/env python3
from flask import Flask, jsonify, render_template, request, redirect
from models import Target, Crash, Packet
from utils import to_base
from proto import Base
import base64
import datetime
app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html',
            target=Target.select().get(),
            crashes=Crash.select().count(),
            unique=Crash.select(Crash.signal,
                Crash.offset,
                Crash.reason,
                Crash.path).distinct().count()
            )

@app.route("/crashes")
def crashes():
    unique_only = request.args.get('unique', False)
    return render_template('crashes.html',
            crashes=Crash.select(),
            unique=Crash.select(Crash.signal,
                Crash.offset,
                Crash.reason,
                Crash.path).distinct(),
            unique_only=unique_only
            )

@app.route("/crash/<int:crash_id>")
def crash(crash_id):
    c = Crash.get(Crash.id==crash_id) 
    packets = [Base(p.data).show(dump=True) for p in c.packets]
    return render_template('crash.html', crash=c, packets=packets)

@app.route("/api/task/start")
def start_task():
    target = Target.select().get()
    target.running = True
    target.started_at = datetime.datetime.now()
    target.save()
    return redirect('/')

@app.route("/api/task/stop")
def stop_task():
    target = Target.select().get()
    target.running = False
    target.save()
    return redirect('/')

@app.route("/api/task/next")
def next_task():
    target = Target.select().get()
    if not target.running:
        return jsonify(status="Target is stopped", task=None)
    start = target.next_sequence
    end = start + 1
    if end > target.last_sequence:
        end = target.last_sequence
    if start >= target.last_sequence:
        return jsonify(status="No more tasks", task=None)
    target.next_sequence = end
    target.save()
    return jsonify(status="OK", task={
        'start': start,
        'end': end,
        'iterations': 100
        })

@app.route("/api/task/<int:task_id>/completed", methods=['POST'])
def mark_completed(task_id):
    target = Target.select().get()
    target.processed += 1
    if target.processed == target.last_sequence:
        target.completed_at = datetime.datetime.now()
    target.save()
    return "OK"

@app.route("/api/crash/submit", methods=['POST'])
def submit():
    data = request.get_json()
    crash = Crash.create(target=Target.select().get(),
            signal=data['signal'],
            reason=data['reason'],
            sequence=data['index'],
            instruction=int(data['instruction'], 16),
            offset=int(data['offset'], 16),
            path=data['path'],
            log=data['log'])
    for i, msg in enumerate(data['testcase']):
        Packet.create(crash=crash, index=i, data=base64.b64decode(msg))
    return "OK"

