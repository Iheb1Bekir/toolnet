#!/usr/bin/env python3
from importlib import import_module
import os
import json
from pathlib import Path
from flask import Flask, Response, jsonify, render_template, request, session
import multiprocessing as mp
import time
import queue
from src.parser import *
from os import listdir
import time
import random
import argparse  # added for extending parser
import uuid
from goal_manager import list_user_goals, load_user_goal, save_user_goal, USER_GOALS_DIR

args = initParser()

# ---- Add --headless if not already present ----
# We extend the parser to include --headless without modifying src/parser.py
parser = argparse.ArgumentParser()
parser.add_argument('--headless', action='store_true', help='Run without GUI')
# Parse known args (ignores unknown) to get headless value
known, unknown = parser.parse_known_args()
args.headless = known.headless
# -------------------------------------------------

queue_from_webapp_to_simulator = mp.Queue()
queue_from_simulator_to_webapp = mp.Queue()
queue_for_error = mp.Queue()
queue_for_execute_to_stop = mp.Queue()
queue_for_execute_is_ongoing = mp.Queue()
queue_for_action_result = mp.Queue()
queue_for_camera_frame = mp.Queue(maxsize=1)
workerId = None
base_url = ""
app = Flask(__name__)
app.secret_key = os.environ.get('TOOLNET_SECRET_KEY', 'toolnet-development-secret')
moves_to_show = []

# All actions that need to be showed on the user screen.
dict_of_predicates = json.load(open("jsons/predicates_for_webapp.json", "r"))["dict_of_predicates"]

# Mapping of user action to the simulator action.
dict_predicate_to_action = json.load(open("jsons/predicates_for_webapp.json","r"))["dict_predicate_to_action"]

# The list of goals that are possible for the simulator to execute.
GOAL_LIST = json.load(open("jsons/predicates_for_webapp.json", "r"))["GOAL_LIST"]

# The list of world instances that can be loaded by the simulator.
WORLD_LIST = json.load(open("jsons/predicates_for_webapp.json", "r"))["WORLD_LIST"]

GOAL_LIST = sorted(set(GOAL_LIST).union(
    str(path).replace('\\', '/') for path in Path('jsons').glob('*_goals/*.json')
))
WORLD_LIST = sorted(set(WORLD_LIST).union(
    str(path).replace('\\', '/') for path in Path('jsons').glob('*_worlds/*.json')
))

def all_goal_paths():
    return list_user_goals()

OBJECT_ALIASES = {'wall': 'walls', 'warehouse_wall': 'wall_warehouse'}

def normalize_object_name(name):
    return OBJECT_ALIASES.get(name, name)

def load_world_objects(world):
    """Return visible object names from a known world file."""
    if world not in WORLD_LIST:
        return []
    with open(world, "r") as handle:
        objects = []
        for entity in json.load(handle).get("entities", []):
            if entity.get("ignore") == "true":
                continue
            objects.append(entity.get("rename", entity.get("name")))
        return sorted(object_name for object_name in objects if object_name)

def load_world_object_names(world):
    """Return both display names and simulator names for validation."""
    if world not in WORLD_LIST:
        return set()
    with open(world, "r") as handle:
        names = set()
        for entity in json.load(handle).get("entities", []):
            if entity.get("ignore") != "true":
                names.add(entity.get("name"))
                names.add(entity.get("rename", entity.get("name")))
        return {name for name in names if name}

def load_goal_objects(goal):
    if goal in list_user_goals():
        return []
    if goal not in GOAL_LIST:
        return []
    with open(goal, "r") as handle:
        data = json.load(handle)
    required = data.get("goal-objects")
    if required is not None:
        return sorted({normalize_object_name(item) for item in required})
    return sorted({normalize_object_name(item) for entry in data.get("goals", []) for item in (entry.get("object"), entry.get("target")) if item})

# Load all objects reqiured
d = json.load(open(args.world))["entities"]
world_objects = []
renamed_objects = {}
constraints_dict = json.load(open("jsons/constraints.json"))
dropdown_states = ["open", "close", "off", "on", "up", "down"]
for obj in d:
    if (("ignore" in obj) and (obj["ignore"] == "true")):
        continue
    if ("rename" in obj):
        world_objects.append(obj["rename"])
        renamed_objects[obj["rename"]] = obj["name"]
    else:
        world_objects.append(obj["name"])
if '3d_printer' in world_objects:
    with open('jsons/objects.json') as file:
        o = json.load(file)["objects"]
    for obj in o:
        if 'Printable' in obj['properties'] and not obj['name'] in world_objects:
            world_objects.append(obj['name'])
world_objects.sort()

def convertActionsFromFile(action_file):
    inp = None
    with open(action_file, 'r') as handle:
        inp = json.load(handle)
    return(inp)

def simulator(queue_from_webapp_to_simulator, queue_from_simulator_to_webapp, queue_for_error, queue_for_execute_to_stop, queue_for_execute_is_ongoing, queue_for_action_result, queue_for_camera_frame):
    """
        The simulator loop accepting inputs from the user and sending it to the simulator.
        Also sends exception the web app for showing.
    """

    import husky_ur5
    import src.actions
    import sys
    husky_ur5.camera_output_queue = queue_for_camera_frame
    husky_ur5.start(args)
    queue_from_simulator_to_webapp.put(True)
    print ("Waiting")
    husky_ur5.firstImage()
    goal_file = None
    while True:
        try:
            inp = queue_from_webapp_to_simulator.get(timeout=1.0 / husky_ur5.SIMULATION_HZ)
        except queue.Empty:
            # Keep the GUI and latest camera frame alive while the web queue is idle.
            husky_ur5.idle_simulation_step()
            continue
        if "set_speed" in inp:
            args.speed = inp["set_speed"]
        elif ("rotate" in inp or "zoom" in inp or "toggle" in inp):
            husky_ur5.changeView(inp["rotate"])
        elif "undo" in inp:
            husky_ur5.undo()
            if (len(moves_to_show) > 0):
                moves_to_show.pop(-1)
        elif "showObject" in inp:
            try:
                husky_ur5.showObject(inp["showObject"])
            except Exception as e:
                print(e)
                queue_for_error.put(str(e))
        elif "restart" in inp:
            goal_file = inp["restart"]
            if goal_file is not None:
                args.goal = goal_file
                if inp.get("world") in WORLD_LIST:
                    args.world = inp["world"]
            elif args.randomize:
                args.goal = random.choice(GOAL_LIST)
                goal_file = args.goal
                args.world = random.choice(WORLD_LIST)
            else:
                goal_file = args.goal
            husky_ur5.destroy()
            del sys.modules["husky_ur5"]
            del sys.modules["src.actions"]
            import husky_ur5
            import src.actions
            husky_ur5.camera_output_queue = queue_for_camera_frame
            husky_ur5.start(args)
            husky_ur5.firstImage()
            queue_from_simulator_to_webapp.put(True)
        else:
            try:
                queue_for_execute_is_ongoing.put(True)
                execution_goal = None if inp.get('playback') else goal_file
                done = husky_ur5.execute(inp, execution_goal, queue_for_execute_to_stop)
                try:
                    queue_for_execute_is_ongoing.get(block=False)
                except:
                    pass
                print("Done: ", done)
                queue_for_action_result.put({'ok': True, 'done': bool(done)})
            except Exception as e:
                print (str(e))
                queue_for_error.put(str(e))
                queue_for_action_result.put({'ok': False, 'error': str(e)})
                done = False
            if (done):
                w = 'factory' if 'factory' in args.world else 'home' if 'home' in args.world else 'outdoor'
                # foldername = 'dataset/home/' + goal_file.split("\\")[3].split(".")[0] + '/' + args.world.split('\\')[3].split(".")[0]
                try: 
                    foldername = 'dataset/' + w + '/' + goal_file.split("\\")[3].split(".")[0] + '/' + args.world.split('\\')[3].split(".")[0]
                except:
                    foldername = 'dataset/' + w + '/' + goal_file.split("/")[-1].split(".")[0] + '/' + args.world.split('/')[-1].split(".")[0]
                try:   
                    a = len(listdir(foldername))
                except Exception as e:
                    os.makedirs(foldername)
                if len(listdir(foldername)) == 0:
                    husky_ur5.saveDatapoint(foldername + '/' + '0')
                else:    
                    husky_ur5.saveDatapoint(foldername + '/' + str(a))
                queue_for_error.put("You have completed this tutorial.")
                queue_from_webapp_to_simulator.put({"restart": args.goal})
            called_undo_before = False

@app.route('/', methods = ["GET"])
def index():
    return render_template(
        'index.html',
        list_of_predicates=dict_of_predicates.keys(),
        workerId=workerId,
        world_objects=world_objects,
        base_url=base_url,
        goals=all_goal_paths(),
        worlds=WORLD_LIST,
        selected_goal=args.goal,
        selected_world=args.world,
    )

@app.route('/start', methods=['POST'])
@app.route('/api/session/start', methods=['POST'])
def start_simulation():
    global args
    data = request.get_json(silent=True) or request.form
    goal = data.get('goal')
    world = data.get('world')
    if (goal not in GOAL_LIST and goal not in list_user_goals()) or world not in WORLD_LIST:
        return jsonify(error='Select a valid goal and world.'), 400
    user_goal = None
    if goal in list_user_goals():
        try:
            user_goal = load_user_goal(goal)
        except (OSError, ValueError) as error:
            return jsonify(error=str(error)), 400
        if user_goal.get('world') and user_goal['world'] != world:
            return jsonify(error='This saved goal belongs to world {}.'.format(user_goal['world'])), 400
        session['playback_actions'] = user_goal['actions']
        session['playback_index'] = 0
    else:
        session.pop('playback_actions', None)
        session.pop('playback_index', None)
    if not set(load_goal_objects(goal)).issubset(load_world_object_names(world)):
        return jsonify(error='Selected goal requires objects missing from the selected world.'), 400
    args.goal = goal
    args.world = world
    queue_from_webapp_to_simulator.put({'restart': goal, 'world': world})
    return jsonify(status='restart_requested', goal=goal, world=world)

@app.route('/reset', methods=['POST'])
def reset_simulation():
    queue_from_webapp_to_simulator.put({'restart': args.goal, 'world': args.world})
    return jsonify(status='reset_requested')

@app.route('/next', methods=['POST'])
def next_action():
    actions = session.get('playback_actions', [])
    index = session.get('playback_index', 0)
    if index >= len(actions):
        return jsonify(error='No saved action remains to execute.'), 409
    result = execute_saved_action(actions[index])
    if not result['ok']:
        return jsonify(error=result['error']), 400
    session['playback_index'] = index + 1
    return jsonify(action=actions[index], index=index + 1, total=len(actions), completed=True)


def execute_saved_action(action):
    if not isinstance(action, dict) or not isinstance(action.get('name'), str):
        return {'ok': False, 'error': 'Invalid saved action.'}
    payload = {'actions': [{'name': action['name'], 'args': action.get('args', [])}], 'playback': True}
    queue_from_webapp_to_simulator.put(payload)
    try:
        return queue_for_action_result.get(timeout=120)
    except Exception:
        return {'ok': False, 'error': 'The simulator did not respond within 120 seconds.'}


@app.route('/run_all', methods=['POST'])
@app.route('/api/session/run-all', methods=['POST'])
def run_all():
    actions = session.get('playback_actions', [])
    index = session.get('playback_index', 0)
    if not actions:
        return jsonify(error='Start a saved goal before running it.'), 409
    for action in actions[index:]:
        result = execute_saved_action(action)
        if not result['ok']:
            return jsonify(error=result['error'], completed=index), 400
        index += 1
        session['playback_index'] = index
    return jsonify(completed=index, total=len(actions), done=True)

@app.route('/get_goals')
def get_goals():
    world = request.args.get('world')
    if not world:
        return jsonify(goals=all_goal_paths())
    available = set(load_world_objects(world))
    goals = [goal for goal in all_goal_paths() if set(load_goal_objects(goal)).issubset(available)]
    return jsonify(goals=goals)


@app.route('/api/goals')
def api_goals():
    return jsonify(goals=all_goal_paths())


@app.route('/api/recording/start', methods=['POST'])
def recording_start():
    session_id = str(uuid.uuid4())
    session['recording_actions'] = []
    session['recording_active'] = True
    session['recording_session_id'] = session_id
    return jsonify(session_id=session_id, actions=[])


@app.route('/api/recording/append', methods=['POST'])
def recording_append():
    if not session.get('recording_active'):
        return jsonify(error='Recording is not active.'), 409
    action = request.get_json(silent=True) or {}
    if not isinstance(action.get('name'), str) or not isinstance(action.get('args', []), list):
        return jsonify(error='Action must contain name and args.'), 400
    actions = session.get('recording_actions', [])
    actions.append({'name': action['name'], 'args': action.get('args', [])})
    session['recording_actions'] = actions
    return jsonify(count=len(actions))


@app.route('/api/recording/stop', methods=['POST'])
def recording_stop():
    actions = session.get('recording_actions', [])
    session['recording_active'] = False
    return jsonify(actions=actions, count=len(actions))


@app.route('/api/goal/save', methods=['POST'])
def goal_save():
    data = request.get_json(silent=True) or {}
    try:
        path, goal = save_user_goal(data.get('name', ''), data.get('world', args.world), data.get('actions', session.get('recording_actions', [])))
    except (TypeError, ValueError, OSError) as error:
        return jsonify(error=str(error)), 400
    session.pop('recording_actions', None)
    session['recording_active'] = False
    return jsonify(path=path, goal=goal)

@app.route('/get_worlds')
def get_worlds():
    return jsonify(worlds=WORLD_LIST)

@app.route('/get_objects_for_world')
def get_objects_for_world():
    return jsonify(objects=load_world_objects(request.args.get('world')))

@app.route('/get_goal_objects')
def get_goal_objects():
    return jsonify(objects=load_goal_objects(request.args.get('goal')))

@app.route('/get_predicates')
def get_predicates():
    return jsonify(predicates={
        name: {
            'action_name': dict_predicate_to_action[name],
            'arguments': [
                {'name': argument, 'type': 'state' if kind == 'dropdown-states' else 'object', 'required': True}
                for argument, kind in definitions.items()
            ],
        }
        for name, definitions in dict_of_predicates.items()
    })

def camera_stream():
    while True:
        try:
            frame = queue_for_camera_frame.get(timeout=1)
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
        except Exception:
            continue

@app.route('/video_feed')
def video_feed():
    return Response(camera_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/set_speed')
def set_speed():
    try:
        args.speed = max(0.1, min(2.0, float(request.args.get('speed', args.speed))))
    except ValueError:
        return jsonify(error='Speed must be numeric.'), 400
    queue_from_webapp_to_simulator.put({'set_speed': args.speed})
    return jsonify(speed=args.speed)

@app.route('/workerId', methods = ["POST"])
def addworkerid():
    global workerId
    workerId = request.form["workerId"]
    print (workerId)
    return ""

@app.route("/arguments")
def return_arguments_for_predicate():
	text = request.args.get('predicate')
	return render_template("arguments.html", arguments_list = list(enumerate(dict_of_predicates[text].items())), world_objects = world_objects, constraints_dict = constraints_dict[text], dropdown_states = dropdown_states)
    
@app.route('/restart_process')
def restart_process():
    try:
        queue_for_execute_is_ongoing.get(block = False)
        queue_for_execute_to_stop.put(True)
        time.sleep(1)
        return "restarted_process_successfully"
    except:
        return "did_not_need_to_restart"

@app.route("/execute_move", methods = ["POST"])
def execute_move():
    print (request.form)
    predicate = request.form.get("predicate")
    if predicate not in dict_predicate_to_action:
        return jsonify(error="Unknown action."), 400
    l = []
    front_end_objects = []
    i = 0
    while True:
        if ("arg" + str(i) in request.form):
            front_end_object = request.form["arg" + str(i)]
            front_end_objects.append(front_end_object)
            if front_end_object in renamed_objects:
                l.append(renamed_objects[front_end_object])
            else:
                l.append(front_end_object)
            i += 1
        else:
            break
    if "Ramp" in predicate or "ramp" in predicate:
        l = []; front_end_objects = []
    d = {
        'actions': [
        {
            'name': str(dict_predicate_to_action[predicate]),
            'args': list(l)
        }
        ]
    }
    missing = [value for value in l if value and value not in load_world_object_names(args.world)]
    if missing:
        return jsonify(error="Object(s) not present in selected world: {}".format(', '.join(missing))), 400
    print (d)
    if len(front_end_objects) > 0:
        move_string = predicate + " ( " + str(front_end_objects[0])
    else:
        move_string = predicate + " ( "
    for i in range(1,len(front_end_objects)):
        move_string += " ," + str(front_end_objects[i])
    move_string += " )"
    print (move_string)
    moves_to_show.append(move_string)
    queue_from_webapp_to_simulator.put(d)
    try:
        result = queue_for_action_result.get(timeout=120)
    except Exception:
        return jsonify(error='The simulator did not respond within 120 seconds.'), 504
    if not result['ok']:
        return jsonify(error=result['error']), 400
    return jsonify(action=d['actions'][0], label=move_string, completed=True)

@app.route("/showObject", methods = ["POST"])
def showObject():
    object_to_show = request.form["object"]
    if object_to_show in renamed_objects:
        object_to_show = renamed_objects[object_to_show]
    print (object_to_show)
    queue_from_webapp_to_simulator.put({"showObject": object_to_show})
    return ""

@app.route("/rotateCameraLeft", methods = ["POST"])
def rotateCameraL():
    queue_from_webapp_to_simulator.put({"rotate": "left"})
    return ""

@app.route("/rotateCameraRight", methods = ["POST"])
def rotateCameraR():
    queue_from_webapp_to_simulator.put({"rotate": "right"})
    return ""

@app.route("/zoomIn", methods = ["POST"])
def zoomIn():
    queue_from_webapp_to_simulator.put({"rotate": "in"})
    return ""

@app.route("/zoomOut", methods = ["POST"])
def zoomOut():
    queue_from_webapp_to_simulator.put({"rotate": "out"})
    return ""

@app.route("/toggle", methods = ["POST"])
def toggle():
    queue_from_webapp_to_simulator.put({"rotate": None})
    return ""

@app.route("/undo_move", methods = ["GET"])
def undo_move():
    queue_from_webapp_to_simulator.put({"undo": True})
    return ""

@app.route("/check_error", methods = ["GET"])
def is_error():
    try:
        err_string = queue_for_error.get(block = False)
        return err_string
    except:
        return ""

if __name__ == '__main__':
    inp = "jsons/input_home.json"
    p = mp.Process(target=simulator, args=(queue_from_webapp_to_simulator,queue_from_simulator_to_webapp,queue_for_error, queue_for_execute_to_stop, queue_for_execute_is_ongoing, queue_for_action_result, queue_for_camera_frame))
    p.start()
    should_webapp_start = queue_from_simulator_to_webapp.get()
    # The ip address where to host the simulator can be changed here.
    app.run(host='0.0.0.0', threaded=True)