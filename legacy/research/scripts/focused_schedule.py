#!/usr/bin/env python3
"""Generate or check an unlocked assignment schedule; never launch a run."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

import focused_tasks as tasks
import verification_review_v2 as json_io

SEED = 'focused-adoption-v1'
TASK_ORDER = ('T1', 'T2', 'T3', 'O1', 'O2', 'O3', 'O4', 'C1', 'C2', 'C3', 'C4')
CONDITIONS = ('none', 'karpathy', 'current', 'focused')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rows_digest(rows):
    return digest(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode())


def pins():
    result = tasks.source_pins()
    root = tasks.TASKS.parents[2]
    for filename in (__file__, json_io.__file__, json_io.v1.__file__):
        path = Path(filename).resolve()
        data = path.read_bytes()
        result[str(path.relative_to(root))] = {'sha256': digest(data), 'bytes': len(data)}
    return result


def variant(task, replicate):
    return 'legacy-locked-task' if task in TASK_ORDER[:3] else tasks.variant_for(task, replicate)


def generate():
    chooser = random.Random(SEED)
    rows = []
    for task in TASK_ORDER:
        for replicate in range(1, 11):
            conditions = list(CONDITIONS)
            chooser.shuffle(conditions)
            for condition in conditions:
                ordinal = len(rows) + 1
                rows.append({'ordinal': ordinal, 'run_id': f'focused-{ordinal:04d}',
                             'task': task, 'replicate': replicate, 'condition': condition,
                             'variant': variant(task, replicate)})
    return {'schema_version': 1, 'draft_test_set': SEED, 'random_seed': SEED,
            'generator_python': '.'.join(map(str, sys.version_info[:3])),
            'status': 'draft_unlocked', 'runtime_ready': False, 'provider_calls': 0,
            'condition_and_runtime_pins_complete': False, 'source_pins': pins(),
            'rows_sha256': rows_digest(rows), 'rows': rows}


def validate(value):
    """Check structure/current source pins without regenerating assignment order."""
    fields = {'schema_version', 'draft_test_set', 'random_seed', 'generator_python',
              'status', 'runtime_ready', 'provider_calls', 'condition_and_runtime_pins_complete',
              'source_pins', 'rows_sha256', 'rows'}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError('invalid schedule fields')
    if (type(value['schema_version']) is not int or value['schema_version'] != 1 or
            value['draft_test_set'] != SEED or value['random_seed'] != SEED or
            not isinstance(value['generator_python'], str) or not value['generator_python'] or
            value['status'] != 'draft_unlocked' or value['runtime_ready'] is not False or
            value['condition_and_runtime_pins_complete'] is not False or
            type(value['provider_calls']) is not int or value['provider_calls'] != 0 or
            value['source_pins'] != pins()):
        raise ValueError('schedule metadata or source pins differ')
    rows = value['rows']
    if not isinstance(rows, list) or len(rows) != 440 or value['rows_sha256'] != rows_digest(rows):
        raise ValueError('schedule membership or row digest differs')
    fields = {'ordinal', 'run_id', 'task', 'replicate', 'condition', 'variant'}
    for block in range(110):
        task, replicate = TASK_ORDER[block // 10], block % 10 + 1
        conditions = []
        for offset, row in enumerate(rows[block * 4:block * 4 + 4]):
            ordinal = block * 4 + offset + 1
            if (not isinstance(row, dict) or set(row) != fields or
                    type(row['ordinal']) is not int or row['ordinal'] != ordinal or
                    row['run_id'] != f'focused-{ordinal:04d}' or row['task'] != task or
                    type(row['replicate']) is not int or row['replicate'] != replicate or
                    not isinstance(row['condition'], str) or row['condition'] not in CONDITIONS or
                    row['variant'] != variant(task, replicate)):
                raise ValueError('schedule row differs from its fixed block')
            conditions.append(row['condition'])
        if set(conditions) != set(CONDITIONS):
            raise ValueError('each block must contain all four conditions once')


def check(path, expected_sha256):
    raw, value = json_io.strict_file_json(path, 'schedule')
    if digest(raw) != expected_sha256:
        raise ValueError('schedule differs from externally supplied file hash')
    validate(value)
    return {'status': 'draft_schedule_valid', 'rows': len(value['rows']),
            'blocks': 110, 'sha256': digest(raw), 'runtime_ready': False,
            'condition_and_runtime_pins_complete': False, 'provider_calls': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('generate')
    create.add_argument('--out', type=Path, required=True)
    verify = commands.add_parser('check')
    verify.add_argument('--schedule', type=Path, required=True)
    verify.add_argument('--sha256', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'generate':
            value = generate()
            validate(value)
            out = tasks.empty_directory(args.out)
            data = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
            (out / 'schedule.json').write_bytes(data)
            result = check(out / 'schedule.json', digest(data))
        else:
            result = check(args.schedule, args.sha256)
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
