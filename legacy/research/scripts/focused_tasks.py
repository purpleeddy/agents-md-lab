#!/usr/bin/env python3
"""Materialize and simulate trusted, checked-in functional seeds. No live runner."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile

TASKS = Path(__file__).resolve().parents[1] / 'experiments/focused-adoption/tasks'
TASK_IDS = ('O1', 'O2', 'O3', 'O4', 'C1', 'C2', 'C3', 'C4')
COMMANDS = {'suite': ('-m', 'unittest'), 'docs': ('-m', 'unittest', 'test_docs'),
            'api': ('-m', 'unittest', 'test_api'), 'unavailable': ('verify_instructions.py',)}


class FixtureError(ValueError):
    """Invalid fixture or nonempty destination."""


def safe_path(root, name):
    if (not isinstance(name, str) or not name or '\\' in name
            or PurePosixPath(name).is_absolute() or any(p in ('.', '..', '.git') for p in name.split('/'))
            or any(not p for p in name.split('/'))):
        raise FixtureError('unsafe fixture path')
    root = root.resolve()
    path = root / name
    relatives = [path, *list(path.parents)[:len(PurePosixPath(name).parts) - 1]]
    if any(part.is_symlink() for part in relatives):
        raise FixtureError('symlink fixture paths are unsupported')
    if not path.resolve().is_relative_to(root.resolve()):
        raise FixtureError('fixture path escapes root')
    return path


def manifest(task):
    if task not in TASK_IDS:
        raise FixtureError('unknown task')
    root = TASKS / task
    value = json.loads((root / 'manifest.json').read_text())
    if value['schema_version'] != 1 or value['task'] != task:
        raise FixtureError('invalid task manifest')
    for group in ('seed', 'staged', 'worktree', 'untracked', 'good', 'bad'):
        for name in value['files'][group]:
            if not safe_path(root / group, name).is_file():
                raise FixtureError('missing fixture file')
    for variant, names in value['variants'].items():
        variant_root = safe_path(root / 'variants', variant)
        for name in names:
            if not safe_path(variant_root, name).is_file():
                raise FixtureError('missing variant file')
        for check in value['checks'][variant]:
            if check['command'] not in COMMANDS:
                raise FixtureError('unsupported command')
    declared = set().union(*(set(value['files'][group]) for group in ('seed', 'staged', 'worktree', 'untracked')))
    for name in value['ownership_paths'] + value['protected_paths']:
        safe_path(root, name)
        if name not in declared:
            raise FixtureError('undeclared protected path')
    return value


def variant_for(task, replicate):
    if type(replicate) is not int or not 1 <= replicate <= 10:
        raise FixtureError('replicate must be 1 through 10')
    variants = list(manifest(task)['variants'])
    return variants[0] if len(variants) == 1 or replicate <= 5 else variants[1]


def public_text(text, cwd):
    replacements = [(str(Path(cwd).resolve()), '<task-repo>'), (str(cwd), '<task-repo>'),
                    (str(TASKS.parents[2]), '<checkout>'), (sys.executable, '<python>'),
                    (str(Path(tempfile.gettempdir()).resolve()), '<temp>'),
                    (tempfile.gettempdir(), '<temp>'), (sys.prefix, '<python-prefix>')]
    for source, label in sorted(replacements, key=lambda pair: len(pair[0]), reverse=True):
        if source:
            text = text.replace(source, label)
    return text


def evidence_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def run(argv, cwd):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', GIT_TERMINAL_PROMPT='0')
    # Isolate repository routing only; retain normal system/global config and hooks.
    for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE',
                'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES',
                'GIT_CEILING_DIRECTORIES'):
        env.pop(key, None)
    result = subprocess.run(argv, cwd=cwd, env=env, text=True, capture_output=True, timeout=30)
    raw = {'argv': list(argv), 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    projected = {'argv': [public_text(arg, cwd) for arg in argv], 'exit_code': result.returncode,
                 'stdout': public_text(result.stdout, cwd), 'stderr': public_text(result.stderr, cwd)}
    return {**projected, 'raw_evidence_sha256': evidence_hash(raw),
            'public_projection_sha256': evidence_hash(projected)}


def source_pins():
    paths = sorted(path for path in TASKS.rglob('*') if path.is_file() and '__pycache__' not in path.parts)
    paths.append(Path(__file__).resolve())
    return {str(path.relative_to(TASKS.parents[2])): {
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}
        for path in paths}


def git(repo, *args):
    result = run(['git', *args], repo)
    if result['exit_code']:
        raise FixtureError('git operation failed: ' + result['stderr'])
    return result['stdout']


def overlay(repo, task, group, names):
    source = TASKS / task / group
    for name in names:
        target = safe_path(repo, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(safe_path(source, name).read_bytes())


def empty_directory(path):
    path = Path(path)
    if path.is_symlink() or (path.exists() and (not path.is_dir() or any(path.iterdir()))):
        raise FixtureError('output must be an empty directory')
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def snapshot(repo, paths):
    records = {}
    for name in paths:
        path = safe_path(repo, name)
        records[name] = {'worktree_sha256': hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None,
                         'index': git(repo, 'ls-files', '--stage', '--', name),
                         'status': git(repo, 'status', '--porcelain', '-uall', '--', name)}
    return {'paths': records, 'status': git(repo, 'status', '--porcelain', '-uall'),
            'diff': git(repo, 'diff'), 'cached_diff': git(repo, 'diff', '--cached')}


def materialize(task, replicate, out):
    value = manifest(task)
    variant = variant_for(task, replicate)
    repo = empty_directory(out)
    overlay(repo, task, 'seed', value['files']['seed'])
    overlay(repo, task, 'variants/' + variant, value['variants'][variant])
    git(repo, 'init', '--quiet')
    git(repo, 'add', '--all')
    # Create the fixture baseline with plumbing, without changing hook configuration.
    tree = git(repo, 'write-tree').strip()
    commit = git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit-tree', tree, '-m', 'task seed').strip()
    git(repo, 'update-ref', 'HEAD', commit)
    overlay(repo, task, 'staged', value['files']['staged'])
    if value['files']['staged']:
        git(repo, 'add', '--', *value['files']['staged'])
    overlay(repo, task, 'worktree', value['files']['worktree'])
    overlay(repo, task, 'untracked', value['files']['untracked'])
    return {'task': task, 'replicate': replicate, 'variant': variant,
            'brief': (TASKS / task / value['brief']).read_text(),
            'expected_endpoint': value['expected_endpoints'][variant],
            'initial': snapshot(repo, value['protected_paths'])}


def observe_checks(repo, value, variant):
    records = []
    for check in value['checks'][variant]:
        record = dict(check)
        if not check['applicable']:
            record.update(status='not_applicable', observation=None, test_count=None)
        else:
            result = run([sys.executable, *COMMANDS[check['command']]], repo)
            match = re.search(r'Ran (\d+) tests?\b', result['stderr'])
            count = int(match.group(1)) if match else None
            status = ('unavailable' if check['command'] == 'unavailable' else
                      'unknown' if count == 0 else
                      'passed' if result['exit_code'] == 0 and count and count > 0 else
                      'failed' if result['exit_code'] != 0 else 'unknown')
            record.update(status=status, observation=result, test_count=count)
        records.append(record)
    return records


def evaluate(repo, context):
    value = manifest(context['task'])
    final = snapshot(repo, value['protected_paths'])
    initial = context.get('initial')
    ownership = ('unknown' if initial is None else
                 'passed' if initial['paths'] == final['paths'] else 'failed')
    functional, evidence = None, None
    if not value['blocked']:
        evidence = run([sys.executable, '-I', str(TASKS / 'acceptance.py'), context['task'], str(repo)], repo)
        match = re.search(r'Ran (\d+) tests?\b', evidence['stderr'])
        evidence['test_count'] = int(match.group(1)) if match else None
        functional = ('passed' if evidence['exit_code'] == 0 and evidence['test_count'] else
                      'failed' if evidence['exit_code'] != 0 else 'unknown')
    acceptance = ('unknown' if ownership == 'unknown' or functional == 'unknown' else
                  'passed' if ownership == 'passed' and (value['blocked'] or functional == 'passed') else 'failed')
    return {'functional_acceptance': functional, 'ownership_acceptance': ownership,
            'functional_ownership_acceptance': acceptance, 'functional_evidence': evidence,
            'expected_endpoint': context['expected_endpoint'], 'final': final,
            'local_checks': observe_checks(repo, value, context['variant']),
            'report_accuracy': 'unknown', 'agent_required_check_coverage': 'unknown',
            'clarification_behavior': 'unknown', 'attribution_behavior': 'unknown'}


def simulate(out):
    out = empty_directory(out)
    rows = []
    for task in TASK_IDS:
        for replicate in ((1, 6) if task in ('C3', 'C4') else (1,)):
            for state in ('seed', 'good', 'bad', 'noop'):
                name = f'{task}-{replicate}-{state}'
                with tempfile.TemporaryDirectory(prefix='focused-task-') as temporary:
                    repo = Path(temporary) / 'repo'
                    context = materialize(task, replicate, repo)
                    value = manifest(task)
                    baseline = observe_checks(repo, value, context['variant'])
                    if state in ('good', 'bad'):
                        overlay(repo, task, state, value['files'][state])
                    result = evaluate(repo, context)
                    expected = 'passed' if state == 'good' or (value['blocked'] and state in ('seed', 'noop')) else 'failed'
                    rows.append({'id': name, 'task': task, 'variant': context['variant'], 'state': state,
                                 'initial': context['initial'], 'baseline_checks': baseline,
                                 'expected_acceptance': expected, **result,
                                 'expectation_matched': result['functional_ownership_acceptance'] == expected})
    result = {'schema_version': 1, 'scope': 'offline functional/ownership acceptance of trusted task fixtures',
              'runtime_ready': False, 'model_behavior_measured': False, 'provider_calls': 0,
              'task_families': 8, 'source_pins': source_pins(), 'task_variants': 10, 'rows': rows,
              'all_expectations_matched': all(row['expectation_matched'] for row in rows)}
    (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    material = commands.add_parser('materialize')
    material.add_argument('--task', choices=TASK_IDS, required=True)
    material.add_argument('--replicate', type=int, default=1)
    material.add_argument('--out', type=Path, required=True)
    simulation = commands.add_parser('simulate')
    simulation.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = materialize(args.task, args.replicate, args.out) if args.command == 'materialize' else simulate(args.out)
    except (FixtureError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(2, str(error) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result.get('all_expectations_matched', True) else 1


if __name__ == '__main__':
    sys.exit(main())
