#!/usr/bin/env python3
"""Offline fixed-check observations; hashes establish consistency, not authenticity."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

try:
    from . import focused_tasks as tasks
except ImportError:
    import focused_tasks as tasks

def pins():
    result = tasks.source_pins()
    root = tasks.TASKS.parents[2]
    for name in ('scripts/focused_observation.py',):
        data = (root / name).read_bytes()
        result[name] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    return result


def runtime():
    return {'python': sys.version, 'executable': '<python>',
            'git': tasks.run(['git', '--version'], tasks.TASKS)['stdout'].strip()}


def state(repo):
    """Logical index and complete regular-file inventory, including ignored files.

    Git internals and bytecode caches are excluded; symlinks/special files fail closed.
    No file contents are exported. This is a sampled state, not a filesystem monitor.
    """
    files = {}
    for path in sorted(repo.rglob('*')):
        relative = path.relative_to(repo)
        if '.git' in relative.parts or '__pycache__' in relative.parts:
            continue
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            files[relative.as_posix()] = {'kind': 'directory', 'mode': stat.S_IMODE(mode)}
        elif stat.S_ISREG(mode):
            if path.name == '.env':
                raise tasks.FixtureError('credential path unsupported')
            data = path.read_bytes()
            files[relative.as_posix()] = {'kind': 'file', 'mode': stat.S_IMODE(mode),
                                        'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        else:
            raise tasks.FixtureError('symlinks and special files unsupported')
    value = {'files': files, 'index': tasks.git(repo, 'ls-files', '--stage', '-z')}
    return {**value, 'sha256': tasks.evidence_hash(value)}


def test_count(evidence):
    matches = re.findall(r'^Ran (\d+) tests? in .+$', evidence['stderr'], re.MULTILINE)
    return int(matches[0]) if len(matches) == 1 else None


class Collector:
    """Parent-owned in-memory collector for disposable trusted fixtures only."""
    def __init__(self, task, replicate, out):
        context = tasks.materialize(task, replicate, out)
        self.repo = Path(out).resolve()
        self.header = {'schema_version': 1, 'task': task, 'replicate': replicate,
                       'variant': context['variant'], 'source_pins': pins(), 'runtime': runtime(),
                       'catalog': tasks.manifest(task)['checks'][context['variant']],
                       'initial': state(self.repo)}
        self.records = []
        self.closed = False

    def _append(self, record):
        if self.closed:
            raise tasks.FixtureError('collector already sealed')
        previous = self.records[-1]['sha256'] if self.records else tasks.evidence_hash(self.header)
        value = {'sequence': len(self.records), 'previous': previous, **record}
        self.records.append({**value, 'sha256': tasks.evidence_hash(value)})

    def checkpoint(self):
        self._append({'kind': 'checkpoint', 'state': state(self.repo)})

    def check(self, identifier, phase='final'):
        if self.closed or phase not in ('baseline', 'final'):
            raise tasks.FixtureError('invalid collector phase')
        check = next((c for c in self.header['catalog'] if c['id'] == identifier), None)
        if check is None or not check['applicable']:
            raise tasks.FixtureError('check absent or inapplicable')
        before = state(self.repo)
        prior = self.records[-1].get('after', self.records[-1].get('state')) if self.records else self.header['initial']
        if before != prior or (phase == 'baseline' and (before != self.header['initial'] or
                any(r['kind'] == 'checkpoint' or r.get('phase') == 'final' for r in self.records))):
            raise tasks.FixtureError('mutation requires checkpoint; baseline must precede edits')
        result = tasks.run([sys.executable, *tasks.COMMANDS[check['command']]], self.repo)
        self._append({'kind': 'check', 'id': identifier, 'phase': phase, 'before': before,
                      'after': state(self.repo), 'evidence': result, 'test_count': test_count(result)})

    def seal(self):
        if self.closed:
            raise tasks.FixtureError('collector already sealed')
        final = state(self.repo)
        prior = self.records[-1].get('after', self.records[-1].get('state')) if self.records else self.header['initial']
        if final != prior:
            raise tasks.FixtureError('final mutation requires checkpoint')
        value = {'count': len(self.records), 'head': self.records[-1]['sha256'] if self.records else tasks.evidence_hash(self.header),
                 'final': final}
        self.closed = True
        return copy.deepcopy({'header': self.header, 'records': self.records,
                              'seal': {**value, 'sha256': tasks.evidence_hash(value)}})


def _hashed(value):
    return isinstance(value, dict) and value.get('sha256') == tasks.evidence_hash(
        {key: item for key, item in value.items() if key != 'sha256'})


def validate(bundle):
    """Reject corruption against current pins; no adversarial producer authentication."""
    try:
        header, records, seal = (bundle[key] for key in ('header', 'records', 'seal'))
        variant = tasks.variant_for(header['task'], header['replicate'])
        catalog = tasks.manifest(header['task'])['checks'][variant]
        if (type(header['schema_version']) is not int or header['schema_version'] != 1 or header['variant'] != variant or
                header['source_pins'] != pins() or header['runtime'] != runtime() or header['catalog'] != catalog or
                not _hashed(header['initial']) or not _hashed(seal) or not _hashed(seal['final']) or
                type(seal['count']) is not int or seal['count'] != len(records)):
            raise tasks.FixtureError('header or seal mismatch')
        previous, current = tasks.evidence_hash(header), header['initial']
        baseline_open = True
        for sequence, record in enumerate(records):
            if not _hashed(record) or type(record['sequence']) is not int or record['sequence'] != sequence or record['previous'] != previous:
                raise tasks.FixtureError('record chain mismatch')
            if record['kind'] == 'checkpoint':
                if not _hashed(record['state']):
                    raise tasks.FixtureError('checkpoint state mismatch')
                current, baseline_open = record['state'], False
            elif record['kind'] == 'check':
                check = next(c for c in catalog if c['id'] == record['id'])
                evidence = record['evidence']
                projected = {k: evidence[k] for k in ('argv', 'exit_code', 'stdout', 'stderr')}
                if (not check['applicable'] or record['phase'] not in ('baseline', 'final') or
                        record['before'] != current or not _hashed(record['after']) or
                        (record['phase'] == 'baseline' and (not baseline_open or current != header['initial'])) or
                        evidence['argv'] != ['<python>', *tasks.COMMANDS[check['command']]] or
                        type(evidence['exit_code']) is not int or
                        not isinstance(evidence['stdout'], str) or not isinstance(evidence['stderr'], str) or
                        not re.fullmatch('[0-9a-f]{64}', evidence['raw_evidence_sha256']) or
                        evidence['public_projection_sha256'] != tasks.evidence_hash(projected) or
                        (record['test_count'] is not None and type(record['test_count']) is not int) or
                        record['test_count'] != test_count(evidence)):
                    raise tasks.FixtureError('command evidence mismatch')
                baseline_open = baseline_open and record['phase'] == 'baseline'
                current = record['after']
            else:
                raise tasks.FixtureError('unknown record kind')
            previous = record['sha256']
        if seal['head'] != previous or seal['final'] != current:
            raise tasks.FixtureError('final state mismatch')
    except (KeyError, TypeError, ValueError, StopIteration, AttributeError) as error:
        raise tasks.FixtureError('invalid observation bundle') from error


def observed_status(record, command):
    if command == 'unavailable':
        evidence = record['evidence']
        missing = ('verify_instructions.py' not in record['before']['files'] and
                   evidence['exit_code'] != 0 and "can't open file" in evidence['stderr'] and
                   'verify_instructions.py' in evidence['stderr'] and
                   '[Errno 2] No such file or directory' in evidence['stderr'])
        return 'unavailable' if missing else 'unknown'
    count, code = record['test_count'], record['evidence']['exit_code']
    return ('unknown' if count == 0 else 'failed' if code != 0 else
            'passed' if count is not None and count > 0 else 'unknown')


def classify(bundle):
    result = {'integrity': 'invalid', 'final_checks': 'unknown', 'checks': [],
              'agent_required_check_coverage': 'unknown', 'report_accuracy': 'unknown', 'agent_cost': 'unknown'}
    try:
        validate(bundle)
    except tasks.FixtureError:
        return result
    result['integrity'] = 'valid'
    for check in bundle['header']['catalog']:
        records = [r for r in bundle['records'] if r['kind'] == 'check' and r['id'] == check['id']]
        baseline = [observed_status(r, check['command']) for r in records if r['phase'] == 'baseline']
        finals = [r for r in records if r['phase'] == 'final']
        status = 'unverified' if not check['applicable'] else 'unknown'
        if finals:
            latest = finals[-1]
            status = observed_status(latest, check['command'])
            if not (latest['before'] == latest['after'] == bundle['seal']['final']):
                status = 'unknown'
        result['checks'].append({**check, 'baseline_statuses': baseline,
                                 'observed_statuses': [observed_status(r, check['command']) for r in records],
                                 'final_status': status})
    statuses = [c['final_status'] for c in result['checks'] if c['applicable']]
    result['final_checks'] = (next((s for s in ('failed', 'unavailable', 'unknown') if s in statuses), 'passed')
                              if statuses else 'unverified')
    return result


SCENARIOS = (
    ('final-pass', 'O4', 1, 'passed'), ('docs-final-pass', 'C1', 1, 'passed'),
    ('baseline-only', 'O4', 1, 'unknown'), ('stale-after-edit', 'C1', 1, 'unknown'),
    ('missing-record', 'C1', 1, 'unknown'), ('corrupt-output', 'C1', 1, 'unknown'),
    ('reordered', 'C1', 1, 'unknown'), ('dropped', 'C1', 1, 'unknown'),
    ('missing-seal', 'C1', 1, 'unknown'), ('zero-tests', 'C1', 1, 'unknown'),
    ('failed-baseline', 'C3', 1, 'failed'), ('failed-mandatory', 'C3', 6, 'failed'),
    ('no-command', 'C4', 1, 'unverified'), ('unavailable', 'C4', 6, 'unavailable'),
)


def simulate(out):
    out = tasks.empty_directory(out)
    rows = []
    for name, task, replicate, expected in SCENARIOS:
        with tempfile.TemporaryDirectory(prefix='focused-observation-') as temporary:
            collector = Collector(task, replicate, Path(temporary) / 'repo')
            catalog = collector.header['catalog']
            identifier = catalog[0]['id'] if catalog else None
            if identifier and name != 'missing-record':
                collector.check(identifier, 'baseline')
            if name != 'baseline-only':
                value = tasks.manifest(task)
                tasks.overlay(collector.repo, task, 'good', value['files']['good'])
                if name == 'zero-tests':
                    (collector.repo / 'test_examples.py').write_text('')
                collector.checkpoint()
                if identifier and name != 'missing-record':
                    collector.check(identifier)
            if name == 'stale-after-edit':
                tasks.overlay(collector.repo, task, 'bad', tasks.manifest(task)['files']['bad'])
                collector.checkpoint()
            bundle = collector.seal()
            if name == 'corrupt-output':
                bundle['records'][-1]['evidence']['stderr'] += 'altered\n'
            elif name == 'reordered':
                bundle['records'].reverse()
            elif name == 'dropped':
                bundle['records'].pop()
            elif name == 'missing-seal':
                bundle.pop('seal')
            actual = classify(bundle)
            expected_integrity = 'invalid' if name in ('corrupt-output', 'reordered', 'dropped', 'missing-seal') else 'valid'
            rows.append({'id': name, 'expected_final_checks': expected, 'expected_integrity': expected_integrity,
                         'actual': actual, 'observations': bundle,
                         'expectation_matched': actual['final_checks'] == expected and actual['integrity'] == expected_integrity})
    result = {'schema_version': 1, 'scope': 'offline parent-owned fixed local-check observations',
              'runtime_ready': False, 'model_behavior_measured': False, 'provider_calls': 0,
              'source_pins': pins(), 'rows': rows,
              'all_expectations_matched': all(r['expectation_matched'] for r in rows)}
    (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    simulation = commands.add_parser('simulate')
    simulation.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = simulate(args.out)
    except (tasks.FixtureError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(2, str(error) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['all_expectations_matched'] else 1


if __name__ == '__main__':
    sys.exit(main())
