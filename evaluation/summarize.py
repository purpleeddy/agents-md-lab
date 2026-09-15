"""Summarize completed pilot files without treating missing measurements as zero."""

import argparse
import json
from pathlib import Path
import statistics


def tokens(record):
    info = record.get('telemetry', {})
    if record['provider'] == 'codex':
        turns = info.get('codex_turn_usage')
        if not turns or any('input_tokens' not in t or 'output_tokens' not in t for t in turns):
            return None
        return sum(t['input_tokens'] + t['output_tokens'] for t in turns)
    usage = info.get('provider_usage')
    fields = ('input_tokens', 'output_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens')
    if not usage or any(field not in usage for field in fields):
        return None
    return sum(usage[field] for field in fields)


def summarize(directories):
    records, plans, seen = [], [], set()
    for directory in directories:
        directory = Path(directory)
        plan = json.loads((directory / 'plan.json').read_text())
        plans.append(plan)
        rows = json.loads((directory / 'results.json').read_text())
        if len(rows) != len(plan['rows']):
            raise ValueError('Run directory is still incomplete: ' + str(directory))
        fields = ("provider", "task", "repeat", "arm")
        planned = {tuple(row[field] for field in fields) for row in plan["rows"]}
        observed = {tuple(row[field] for field in fields) for row in rows}
        if planned != observed or len(planned) != len(rows):
            raise ValueError("Results do not match planned trials: " + str(directory))
        for record in rows:
            key = tuple(record[field] for field in ('provider', 'task', 'repeat', 'arm'))
            if key in seen:
                raise ValueError('Duplicate trial; do not mix calibration and final runs.')
            seen.add(key)
            records.append(record)
    for field in ('baseline_sha256', 'fixture_sha256', 'effort', 'models', 'seed'):
        if any(plan[field] != plans[0][field] for plan in plans):
            raise ValueError('Incompatible experiment plans: ' + field)
    for provider in {r['provider'] for r in records}:
        versions = {plan.get('cli_versions', {}).get(provider) for plan in plans
                    if any(row['provider'] == provider for row in plan['rows'])}
        if len(versions) > 1:
            raise ValueError('Incompatible CLI versions: ' + provider)
    result = {'baseline_sha256': plans[0]['baseline_sha256'], 'fixture_sha256': plans[0]['fixture_sha256'],
              'human_review': 'unverified', 'arms': [], 'pairs': []}
    for provider in sorted({r['provider'] for r in records}):
        for arm in ('control', 'baseline'):
            rows = [r for r in records if r['provider'] == provider and r['arm'] == arm]
            attempted = [r for r in rows if r['status'] != 'not_run_provider_blocked']
            counts = [tokens(r) for r in attempted]
            times = [r.get('elapsed_seconds') for r in attempted]
            result['arms'].append(dict(provider=provider, arm=arm, planned=len(rows), attempted=len(attempted),
                completed=sum(r['status'] == 'completed' for r in rows),
                functional_pass=sum(r.get('functional_pass') is True for r in rows),
                total_tokens=sum(counts) if counts and all(n is not None for n in counts) else None,
                median_seconds=statistics.median(times) if times and all(t is not None for t in times) else None,
                missing_usage=sum(n is None for n in counts)))
        keys = sorted({(r['task'], r['repeat']) for r in records if r['provider'] == provider})
        for task, repeat in keys:
            pair = {r['arm']: r for r in records if (r['provider'], r['task'], r['repeat']) == (provider, task, repeat)}
            if set(pair) != {'control', 'baseline'}:
                raise ValueError('Missing A/B arm: ' + provider + '/' + task)
            a, b = pair['control'], pair['baseline']
            ta, tb = tokens(a), tokens(b)
            result['pairs'].append(dict(provider=provider, task=task, repeat=repeat,
                control_pass=a.get('functional_pass'), baseline_pass=b.get('functional_pass'),
                token_difference=tb - ta if ta is not None and tb is not None else None,
                seconds_difference=b['elapsed_seconds'] - a['elapsed_seconds']
                    if 'elapsed_seconds' in a and 'elapsed_seconds' in b else None))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories', nargs='+', type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.directories), indent=2))
