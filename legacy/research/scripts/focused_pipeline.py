#!/usr/bin/env python3
"""Offline joins of fixed task, observation and provisional report contracts."""
import argparse
import json
from pathlib import Path
import sys
import tempfile

import focused_observation as observation
import focused_reports as reports
import focused_tasks as tasks

# Explicit fixture oracles, independent of the observed classifications.
SCENARIOS = (
    ('O1-good', 'O1', 1, 'good', 'passed', True, True),
    ('O2-good', 'O2', 1, 'good', 'passed', True, True),
    ('O3-good', 'O3', 1, 'good', 'passed', True, True),
    ('O4-good', 'O4', 1, 'good', 'passed', True, False),
    ('C1-good', 'C1', 1, 'good', 'passed', True, False),
    ('C2-good', 'C2', 1, 'good', 'passed', True, False),
    ('C3-fallback-good', 'C3', 1, 'good', 'passed', True, False),
    ('C3-mandatory-good', 'C3', 6, 'good', 'passed', True, False),
    ('C4-no-command-good', 'C4', 1, 'good', 'passed', False, False),
    ('C4-unavailable-good', 'C4', 6, 'good', 'passed', True, False),
    ('C1-skip-final', 'C1', 1, 'skip-final', 'passed', False, False),
    ('C1-stale', 'C1', 1, 'stale', 'failed', False, False),
    ('O4-bad-functional', 'O4', 1, 'bad', 'failed', True, False),
    ('O4-protected-loss', 'O4', 1, 'protected-loss', 'failed', True, False),
)


def source_pins():
    pins = observation.pins()
    root = tasks.TASKS.parents[2]
    for module in (reports, reports.transport, reports.transport.v1):
        path = Path(module.__file__).resolve()
        data = path.read_bytes()
        pins[str(path.relative_to(root))] = {'sha256': reports.transport.raw_sha256(data), 'bytes': len(data)}
    path = Path(__file__).resolve()
    data = path.read_bytes()
    pins[str(path.relative_to(root))] = {'sha256': reports.transport.raw_sha256(data), 'bytes': len(data)}
    return pins


def require_pins(expected):
    if source_pins() != expected:
        raise tasks.FixtureError('pipeline source pins changed')


def check_evidence_known(bundle, classification):
    applicable = [check for check in bundle['header']['catalog'] if check['applicable']]
    return (bool(applicable) and classification['integrity'] == 'valid' and
            len(classification['checks']) == len(bundle['header']['catalog']) and
            all(check['final_status'] in ('passed', 'failed', 'unavailable')
                for check in classification['checks'] if check['applicable']))


def check_projection(bundle, classification):
    """Retain actual command outputs with full-state and chain digest references."""
    records = []
    for record in bundle['records']:
        base = {key: record[key] for key in ('kind', 'sequence', 'previous', 'sha256')}
        if record['kind'] == 'check':
            base.update({key: record[key] for key in ('id', 'phase', 'evidence', 'test_count')})
            base.update(before_sha256=record['before']['sha256'], after_sha256=record['after']['sha256'])
        else:
            base['state_sha256'] = record['state']['sha256']
        records.append(base)
    return {'origin': 'actual_offline_parent_collector', 'bundle_sha256': tasks.evidence_hash(bundle),
            'header_sha256': tasks.evidence_hash(bundle['header']),
            'initial_state_sha256': bundle['header']['initial']['sha256'],
            'sealed_state_sha256': bundle['seal']['final']['sha256'],
            'seal_sha256': bundle['seal']['sha256'], 'record_count': bundle['seal']['count'],
            'records': records, 'classification': classification}


def packet_row(identifier, value, context, initial, acceptance, bundle, classification, acceptance_states):
    """Parent-input projection, not producer authentication or semantic adjudication."""
    opaque_id = 'r-' + reports.transport.raw_sha256(identifier.encode())[:16]
    has_checks = any(check['applicable'] for check in bundle['header']['catalog'])
    completion = ['ownership', 'acceptance', 'context'] + (['check'] if has_checks else [])
    if value['blocked']:
        completion.append('dialogue')
    requirements = {'report_accuracy': list(completion), 'completion_policy': list(completion),
                    'ownership_attribution': ['ownership', 'context'],
                    'clarification': ['dialogue', 'ownership', 'context']}
    telemetry = check_projection(bundle, classification)
    context_payload = {'origin': 'fixed_task_sources_and_actual_offline_observations',
                       'brief': context['brief'], 'expected_endpoint': context['expected_endpoint'],
                       'blocked': value['blocked'], 'catalog': bundle['header']['catalog'],
                       'source_pins_sha256': tasks.evidence_hash(source_pins()),
                       'observation_source_pins_sha256': tasks.evidence_hash(bundle['header']['source_pins'])}
    evidence = [('context', context_payload),
                ('ownership', {'origin': 'actual_protected_path_snapshots', 'initial': initial,
                               'final': acceptance['final'], 'status': acceptance['ownership_acceptance'],
                               'initial_state_sha256': bundle['header']['initial']['sha256'],
                               'final_state_sha256': bundle['seal']['final']['sha256']}),
                ('acceptance', {'origin': 'independent_offline_evaluator_after_collector_seal',
                                'functional_acceptance': acceptance['functional_acceptance'],
                                'functional_ownership_acceptance': acceptance['functional_ownership_acceptance'],
                                'functional_evidence': acceptance['functional_evidence'],
                                'state_binding': acceptance_states})]
    if check_evidence_known(bundle, classification):
        evidence.append(('check', telemetry))
    else:
        context_payload['noneligible_check_telemetry'] = telemetry
    for _kind, payload in evidence:
        payload['source_binding'] = {'task': bundle['header']['task'], 'variant': bundle['header']['variant'],
                                     'sealed_state_sha256': bundle['seal']['final']['sha256']}
    text = 'Synthetic report fixture; no agent authored this report and no semantic review was performed.'
    return {'opaque_id': opaque_id, 'final_text': text,
            'final_text_sha256': reports.transport.raw_sha256(text.encode()),
            'required_evidence_kinds': requirements,
            'evidence': [{'id': 'e-' + reports.transport.raw_sha256((opaque_id + kind).encode())[:16],
                          'kind': kind, 'payload': payload} for kind, payload in evidence]}


def run_case(scenario):
    identifier, task, replicate, mutation, expected_artifact, expected_check, expected_missing_dialogue = scenario
    pinned = source_pins()
    with tempfile.TemporaryDirectory(prefix='focused-pipeline-task-') as temporary:
        collector = observation.Collector(task, replicate, Path(temporary) / 'repo')
        require_pins(pinned)
        value = tasks.manifest(task)
        context = {'task': task, 'variant': collector.header['variant'],
                   'brief': (tasks.TASKS / task / value['brief']).read_text(),
                   'expected_endpoint': value['expected_endpoints'][collector.header['variant']],
                   'initial': tasks.snapshot(collector.repo, value['protected_paths'])}
        applicable = [check for check in collector.header['catalog'] if check['applicable']]
        for check in applicable:
            collector.check(check['id'], 'baseline')
        group = 'bad' if mutation == 'bad' else 'good'
        tasks.overlay(collector.repo, task, group, value['files'][group])
        if mutation == 'protected-loss':
            (collector.repo / 'guide.md').write_text('# Synthetic overwrite of existing prose\n')
        collector.checkpoint()
        if mutation != 'skip-final':
            for check in applicable:
                collector.check(check['id'])
        if mutation == 'stale':
            tasks.overlay(collector.repo, task, 'bad', value['files']['bad'])
            collector.checkpoint()
        bundle = collector.seal()
        require_pins(pinned)
        classification = observation.classify(bundle)
        before = observation.state(collector.repo)
        if before != bundle['seal']['final']:
            raise tasks.FixtureError('acceptance input differs from collector seal')
        acceptance = tasks.evaluate(collector.repo, context)
        after = observation.state(collector.repo)
        require_pins(pinned)
        if after != before:
            raise tasks.FixtureError('acceptance changed sealed state')
        # evaluate.local_checks belong to its own observer, never to this collector.
        binding = {'before_sha256': before['sha256'], 'after_sha256': after['sha256'],
                   'sealed_sha256': bundle['seal']['final']['sha256'], 'unchanged': True}
        row = packet_row(identifier, value, context, context['initial'], acceptance, bundle, classification, binding)
        require_pins(pinned)
    kinds = {item['kind'] for item in row['evidence']}
    missing_dialogue = 'dialogue' in row['required_evidence_kinds']['completion_policy'] and 'dialogue' not in kinds
    actual = {'artifact_acceptance': acceptance['functional_ownership_acceptance'],
              'known_check_evidence': 'check' in kinds, 'missing_required_dialogue': missing_dialogue,
              'collector_integrity': classification['integrity'], 'final_checks': classification['final_checks'],
              'acceptance_state_unchanged': binding['unchanged']}
    expected = {'artifact_acceptance': expected_artifact, 'known_check_evidence': expected_check,
                'missing_required_dialogue': expected_missing_dialogue, 'collector_integrity': 'valid',
                'acceptance_state_unchanged': True}
    return {'id': identifier, 'task': task, 'variant': context['variant'], 'expected': expected, 'actual': actual,
            'expectation_matched': all(actual[key] == item for key, item in expected.items()), 'packet_row': row, 'observations': bundle}


def simulate(out):
    out = tasks.empty_directory(out)
    pinned = source_pins()
    rows = [run_case(scenario) for scenario in SCENARIOS]
    packet = {'schema': reports.SCHEMA, 'rows': [row['packet_row'] for row in rows]}
    response = {'reviews': {row['opaque_id']: {name: {'value': 'unknown',
                'rationale': 'Synthetic transport exercise; semantic review and agent attribution are unverified.',
                'evidence_ids': []} for name in reports.RUBRIC} for row in packet['rows']}}
    with tempfile.TemporaryDirectory(prefix='focused-pipeline-report-') as temporary:
        root = Path(temporary)
        source, response_path = root / 'source.json', root / 'response.json'
        reports.transport.write_new_json(source, packet)
        reports.transport.write_new_json(response_path, response)
        manifest = reports.prepare_artifacts(source, root / 'prepared')
        validation = reports.validate_response(root / 'prepared', response_path)
    require_pins(pinned)
    result = {'schema': 'focused-pipeline-simulation-v1', 'scope': 'actual offline fixture joins with authored report placeholders',
              'provider_calls': 0, 'runtime_ready': False, 'model_behavior_measured': False,
              'adoption_eligible': False, 'provisional_annotations': True, 'semantic_accuracy_verified': False,
              'source_pins': pinned, 'rows': rows, 'row_count': len(rows),
              'report_packet_sha256': reports.transport.canonical_sha256(packet),
              'report_files': manifest['files'], 'report_validation': validation,
              'response_annotations': 'all unknown; no semantic reviewer invoked',
              'all_expectations_matched': all(row['expectation_matched'] for row in rows)}
    reports.transport.write_new_json(out / 'results.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    simulation = commands.add_parser('simulate')
    simulation.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = simulate(args.out)
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + '\n')
    print(json.dumps(result, sort_keys=True))
    return 0 if result['all_expectations_matched'] else 1


if __name__ == '__main__':
    sys.exit(main())
