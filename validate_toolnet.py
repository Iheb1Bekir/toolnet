import json
from pathlib import Path

ROOT = Path(__file__).parent
PREDICATES_FILE = ROOT / 'jsons' / 'predicates_for_webapp.json'
OBJECT_ALIASES = {'wall': 'walls', 'warehouse_wall': 'wall_warehouse'}


def world_objects(path):
    data = json.loads(path.read_text())
    return {
        name
        for entity in data.get('entities', [])
        if entity.get('ignore') != 'true'
        for name in {entity.get('name'), entity.get('rename', entity.get('name'))}
        if name
    }


def goal_objects(path):
    data = json.loads(path.read_text())
    if data.get('goal-objects') is not None:
        return {OBJECT_ALIASES.get(name, name) for name in data['goal-objects']}
    return {
        name
        for item in data.get('goals', [])
        for name in (item.get('object'), item.get('target'))
        if name
        for name in [OBJECT_ALIASES.get(name, name)]
    }


def main():
    metadata = json.loads(PREDICATES_FILE.read_text())
    definitions = metadata['dict_of_predicates']
    actions = metadata['dict_predicate_to_action']
    errors = []

    for predicate, arguments in definitions.items():
        if predicate not in actions:
            errors.append(f'predicate has no action mapping: {predicate}')
        for argument, argument_type in arguments.items():
            if argument_type not in {'dropdown-objects', 'dropdown-states'}:
                errors.append(f'unsupported argument type {argument_type!r} in {predicate}: {argument}')

    worlds = sorted((ROOT / 'jsons').glob('*_worlds/*.json'))
    goals = sorted((ROOT / 'jsons').glob('*_goals/*.json'))
    compatible = 0
    for goal in goals:
        required = goal_objects(goal)
        if not any(required <= world_objects(world) for world in worlds):
            errors.append(f'goal has no compatible world: {goal.relative_to(ROOT)}')
        compatible += sum(required <= world_objects(world) for world in worlds)

    if errors:
        for error in errors:
            print(f'ERROR: {error}')
        return 1
    print(f'Validated {len(worlds)} worlds, {len(goals)} goals, {len(definitions)} predicates.')
    print(f'Compatible goal/world pairs: {compatible}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
