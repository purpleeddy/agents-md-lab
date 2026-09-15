"""Focused transport contract tests; synthetic assertions are not adjudicated facts."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import focused_reports as reports


class FocusedReportsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = reports.synthetic_packet()
        cls.response = reports.synthetic_response(cls.packet)

    def test_complete_440_membership_and_batch_size(self):
        self.assertEqual(len(reports.annotations(self.packet, self.response)), 440)
        with tempfile.TemporaryDirectory() as temporary:
            result = reports.simulate(Path(temporary) / 'out')
            self.assertEqual(result['batch_count'], 11)
            self.assertEqual(result['batch_size'], 40)
            self.assertTrue(all(b['rows'] == 40 and b['status'] == 'contract_valid' for b in result['batches']))
            self.assertTrue(result['full_response_membership_valid'])
            self.assertEqual(result['provider_calls'], 0)
            for key in ('runtime_ready', 'model_behavior_measured', 'semantic_accuracy_verified',
                        'adoption_eligible', 'legacy_scoring_verified', 'actual_model_packet_size_verified'):
                self.assertFalse(result[key])
            self.assertTrue(result['provisional_annotations'])
            self.assertGreater(result['max_packet_bytes'], 0)
            self.assertGreater(result['max_schema_bytes'], 0)
            self.assertGreater(result['max_response_bytes'], 0)
            self.assertNotIn(str(ROOT), json.dumps(result))

    def test_exact_membership_missing_extra_and_criterion(self):
        for action in ('missing', 'extra', 'criterion', 'nested'):
            response = copy.deepcopy(self.response)
            identifier = self.packet['rows'][1]['opaque_id']
            if action == 'missing':
                response['reviews'].pop(identifier)
            elif action == 'extra':
                response['reviews']['r-' + '0' * 16] = response['reviews'][identifier]
            elif action == 'criterion':
                response['reviews'][identifier].pop('report_accuracy')
            else:
                response['reviews'][identifier]['report_accuracy']['extra'] = 1
            with self.assertRaises(ValueError):
                reports.annotations(self.packet, response)

    def test_duplicate_json_nonfinite_and_truncated_rejected(self):
        for raw in (b'{"reviews":{},"reviews":{}}', b'{"reviews":', b'{"x":NaN}', b'\xff'):
            with self.assertRaises(ValueError):
                reports.transport.strict_json(raw, 'response')

    def test_cross_row_and_duplicate_citations_rejected(self):
        row = self.packet['rows'][1]
        for ids in ([self.packet['rows'][2]['evidence'][0]['id']], [row['evidence'][0]['id']] * 2):
            response = copy.deepcopy(self.response)
            response['reviews'][row['opaque_id']]['report_accuracy']['evidence_ids'] = ids
            with self.assertRaises(ValueError):
                reports.annotations(self.packet, response)

    def test_wrong_kind_and_declared_prerequisites_rejected(self):
        for index, missing in ((1, 'dialogue'), (2, 'context'), (6, 'check')):
            row = self.packet['rows'][index]
            self.assertIsNotNone(row['final_text'])
            response = copy.deepcopy(self.response)
            annotation = response['reviews'][row['opaque_id']]['completion_policy']
            annotation['value'] = 'pass'
            annotation['evidence_ids'] = [e['id'] for e in row['evidence'] if e['kind'] != missing]
            with self.assertRaises(ValueError):
                reports.annotations(self.packet, response)
        row = self.packet['rows'][6]
        response = copy.deepcopy(self.response)
        response['reviews'][row['opaque_id']]['ownership_attribution']['evidence_ids'] = [
            e['id'] for e in row['evidence'] if e['kind'] == 'check']
        with self.assertRaises(ValueError):
            reports.annotations(self.packet, response)

    def test_no_check_blocked_and_no_command_can_be_known(self):
        for index in (1, 2):
            row = self.packet['rows'][index]
            self.assertNotIn('check', {e['kind'] for e in row['evidence']})
            annotation = self.response['reviews'][row['opaque_id']]['completion_policy']
            self.assertEqual(annotation['value'], 'pass')
        self.assertEqual(self.response['reviews'][self.packet['rows'][1]['opaque_id']]['clarification']['value'], 'pass')
        reports.annotations(self.packet, self.response)

    def test_missing_report_and_zero_evidence_force_unknown(self):
        for index in (0, 4):
            row = self.packet['rows'][index]
            self.assertTrue(all(a['value'] == 'unknown' for a in self.response['reviews'][row['opaque_id']].values()))
            response = copy.deepcopy(self.response)
            response['reviews'][row['opaque_id']]['report_accuracy']['value'] = 'pass'
            with self.assertRaises(ValueError):
                reports.annotations(self.packet, response)
        packet = copy.deepcopy(self.packet)
        packet['rows'][1]['final_text'] = None
        with self.assertRaises(ValueError):
            reports.source_rows(packet)

    def test_unknown_can_omit_evidence_but_known_cannot(self):
        response = copy.deepcopy(self.response)
        row = self.packet['rows'][1]
        annotation = response['reviews'][row['opaque_id']]['report_accuracy']
        annotation.update(value='unknown', evidence_ids=[])
        reports.annotations(self.packet, response)
        annotation['value'] = 'fail'
        with self.assertRaises(ValueError):
            reports.annotations(self.packet, response)

    def test_packet_hash_types_ids_and_condition_metadata_rejected(self):
        mutations = (
            lambda p: p['rows'][1].__setitem__('final_text', 'changed'),
            lambda p: p['rows'][1].__setitem__('opaque_id', 'focused-1'),
            lambda p: p['rows'][1].__setitem__('opaque_id', p['rows'][0]['opaque_id']),
            lambda p: p['rows'][1]['evidence'][0].__setitem__('id', p['rows'][0]['evidence'][0]['id']),
            lambda p: p['rows'][1]['evidence'][0].__setitem__('kind', 'invented'),
            lambda p: p['rows'][1]['evidence'][0]['payload'].__setitem__('condition_label', 'focused'),
            lambda p: p['rows'][1]['evidence'][0]['payload'].__setitem__('nested', [{'arm': 'current'}]),
            lambda p: p['rows'][1]['required_evidence_kinds'].__setitem__('completion_policy', []),
        )
        for mutation in mutations:
            packet = copy.deepcopy(self.packet)
            mutation(packet)
            with self.assertRaises(ValueError):
                reports.source_rows(packet)

    def test_schema_has_exact_membership_and_null_report_unknown(self):
        schema = reports.response_schema(self.packet)
        reviews = schema['properties']['reviews']
        self.assertEqual(len(reviews['required']), 440)
        self.assertFalse(reviews['additionalProperties'])
        first = reviews['properties'][self.packet['rows'][0]['opaque_id']]
        for criterion in reports.RUBRIC:
            self.assertEqual(first['properties'][criterion]['properties']['value']['enum'], ['unknown'])
        self.assertFalse(first['additionalProperties'])

    def test_prepared_roundtrip_and_all_artifact_tampering(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, response = root / 'source.json', root / 'response.json'
            packet = {'schema': reports.SCHEMA, 'rows': self.packet['rows'][:40]}
            reports.transport.write_new_json(source, packet)
            reports.transport.write_new_json(response, reports.synthetic_response(packet))
            prepared = root / 'prepared'
            manifest = reports.prepare_artifacts(source, prepared)
            self.assertEqual(len(manifest['source_pins']), 3)
            result = reports.validate_response(prepared, response)
            self.assertEqual(result['status'], 'contract_valid')
            self.assertTrue(result['provisional_annotations'])
            self.assertFalse(result['adoption_eligible'])
            with self.assertRaises(ValueError):
                reports.prepare_artifacts(source, prepared)
            for name in (*reports.NAMES, reports.MANIFEST):
                path = prepared / name
                original = path.read_bytes()
                path.write_bytes(original + b'\n')
                with self.assertRaises(ValueError):
                    reports.validate_response(prepared, response)
                path.write_bytes(original)
            manifest_path = prepared / reports.MANIFEST
            manifest['source_pins']['focused_reports.py'] = '0' * 64
            manifest_path.write_bytes(reports.transport.json_bytes(manifest) + b'\n')
            with self.assertRaises(ValueError):
                reports.validate_response(prepared, response)

    def test_cli_has_no_live_or_import_entrypoint(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/focused_reports.py'), '--help'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('{prepare,validate,simulate}', result.stdout)

    def test_all_annotations_need_nonempty_reason(self):
        for value in ('pass', 'fail', 'unknown'):
            response = copy.deepcopy(self.response)
            row = self.packet['rows'][1]
            annotation = response['reviews'][row['opaque_id']]['report_accuracy']
            annotation.update(value=value, rationale='  \n ')
            with self.assertRaises(ValueError):
                reports.annotations(self.packet, response)

    def test_blank_report_keeps_hash_but_forces_unknown(self):
        for text in ('', ' \n\t '):
            packet = copy.deepcopy(self.packet)
            row = packet['rows'][1]
            row['final_text'] = text
            row['final_text_sha256'] = reports.transport.raw_sha256(text.encode())
            reports.source_rows(packet)
            schema = reports.response_schema(packet)
            properties = schema['properties']['reviews']['properties'][row['opaque_id']]['properties']
            for name in reports.RUBRIC:
                self.assertEqual(properties[name]['properties']['value']['enum'], ['unknown'])
            unknown = reports.synthetic_response(packet)
            reports.annotations(packet, unknown)
            for name in reports.RUBRIC:
                response = copy.deepcopy(unknown)
                response['reviews'][row['opaque_id']][name].update(
                    value='pass', evidence_ids=[e['id'] for e in row['evidence']])
                with self.assertRaises(ValueError):
                    reports.annotations(packet, response)
