"""Offline contract checks for future structured verification-review transport."""

import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import verification_review as v1  # noqa: E402
import verification_review_v2 as v2  # noqa: E402


class ReviewV2Fixture:
    def row(self, opaque_id, text, event_ids):
        return {
            "opaque_id": opaque_id,
            "final_text": text,
            "final_text_sha256": v1.text_hash(text) if text is not None else None,
            "final_text_display_sha256": v1.text_hash(text) if text is not None else None,
            "verification": {"events": [{"event_id": event_id} for event_id in event_ids]},
            "review_joinable": bool(event_ids),
        }

    def packet(self, absent_final_text=False):
        return {
            "schema": v2.V1_PACKET_SCHEMA,
            "reviewer_instructions": {
                "no_tools": True,
                "purpose": "v1 source fixture",
                "blinding": "v1 source fixture has no labels",
                "zero_event_rows": "unknown without IDs",
                "response": {"format": "obsolete v1 array", "one_entry_per_opaque_id": True},
            },
            "rubric": v1.RUBRIC,
            "rows": [
                self.row("review-observed", "displayed report", ["event-observed"]),
                self.row("review-zero", None if absent_final_text else "zero report", []),
            ],
        }

    def response(self, packet):
        return {
            "reviews": {
                row["opaque_id"]: {
                    "evidence_event_ids": [row["verification"]["events"][0]["event_id"]]
                    if row["verification"]["events"] else [],
                    "annotations": {
                        name: {"value": "unknown", "rationale": "fixture"}
                        for name in v1.ANNOTATIONS
                    },
                }
                for row in packet["rows"]
            },
        }

    def write_json(self, path, value):
        Path(path).write_bytes(v2.json_bytes(value) + b"\n")

    def prepare(self, temporary, packet=None):
        packet = self.packet() if packet is None else packet
        source = Path(temporary) / "packet.json"
        self.write_json(source, packet)
        prepared = Path(temporary) / "prepared"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(v2.main(["prepare", "--packet", str(source), "--out", str(prepared)]), 0)
        return packet, source, prepared


class ReviewV2Test(unittest.TestCase, ReviewV2Fixture):
    def assert_schema_contract(self, schema):
        allowed = {"type", "properties", "required", "additionalProperties", "items", "enum", "minItems"}

        def visit(node):
            self.assertIsInstance(node, dict)
            self.assertTrue(set(node).issubset(allowed))
            if node.get("type") == "object":
                self.assertEqual(set(node), {"type", "properties", "required", "additionalProperties"})
                self.assertIsInstance(node["properties"], dict)
                self.assertEqual(set(node["required"]), set(node["properties"]))
                self.assertEqual(len(node["required"]), len(node["properties"]))
                self.assertFalse(node["additionalProperties"])
                for child in node["properties"].values():
                    visit(child)
            elif node.get("type") == "array":
                self.assertEqual(set(node), {"type", "items", "minItems"})
                self.assertIn(node["minItems"], (0, 1))
                visit(node["items"])
            else:
                self.assertEqual(node.get("type"), "string")
                self.assertTrue(set(node).issubset({"type", "enum"}))
                if "enum" in node:
                    self.assertTrue(node["enum"])
                    self.assertTrue(all(isinstance(value, str) for value in node["enum"]))

        visit(schema)

    def test_prepare_writes_four_pinned_artifacts_and_supported_keyed_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet, source, prepared = self.prepare(temporary, self.packet(absent_final_text=True))
            self.assertEqual({path.name for path in prepared.iterdir()}, v2.PREPARED_NAMES)
            source_raw = source.read_bytes()
            copied = (prepared / v2.SOURCE_PACKET_NAME).read_bytes()
            derived = v2.strict_json((prepared / v2.V2_PACKET_NAME).read_bytes(), "derived")
            schema = v2.strict_json((prepared / v2.RESPONSE_SCHEMA_NAME).read_bytes(), "schema")
            manifest = v2.strict_json((prepared / v2.PREPARATION_NAME).read_bytes(), "manifest")
        self.assertEqual(copied, source_raw)
        self.assertEqual(derived["rows"], packet["rows"])
        self.assertEqual(derived["rubric"], v1.RUBRIC)
        self.assert_schema_contract(schema)
        self.assertEqual(set(derived["reviewer_instructions"]), {
            "no_tools", "purpose", "blinding", "zero_event_rows", "response",
        })
        self.assertTrue(derived["reviewer_instructions"]["response"]["host_binds_final_text_sha256"])
        reviews = schema["properties"]["reviews"]
        self.assertEqual(reviews["required"], ["review-observed", "review-zero"])
        self.assertFalse(reviews["additionalProperties"])
        observed = reviews["properties"]["review-observed"]
        zero = reviews["properties"]["review-zero"]
        self.assertEqual(observed["properties"]["evidence_event_ids"]["minItems"], 1)
        self.assertEqual(observed["properties"]["evidence_event_ids"]["items"]["enum"], ["event-observed"])
        self.assertEqual(zero["properties"]["evidence_event_ids"], {
            "type": "array", "items": {"type": "string"}, "minItems": 0,
        })
        self.assertEqual(
            zero["properties"]["annotations"]["properties"]["report_accuracy"]["properties"]["value"]["enum"],
            ["unknown"],
        )
        for row in packet["rows"]:
            value = reviews["properties"][row["opaque_id"]]
            annotations = value["properties"]["annotations"]
            self.assertEqual(set(annotations["properties"]), set(v1.ANNOTATIONS))
            expected_values = ["unknown"] if not row["verification"]["events"] else list(v2.VALID_VALUES)
            for name in v1.ANNOTATIONS:
                annotation = annotations["properties"][name]
                self.assertEqual(annotation["required"], ["value", "rationale"])
                self.assertEqual(annotation["properties"]["value"]["enum"], expected_values)
        self.assertEqual(manifest["source_packet"]["raw_sha256"], v2.raw_sha256(source_raw))
        self.assertEqual(manifest["source_packet"]["canonical_sha256"], v2.canonical_sha256(packet))
        self.assertFalse(manifest["runtime_verified"])

    def test_validate_host_binds_hashes_in_memory_without_importing_a_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet, _source, prepared = self.prepare(temporary, self.packet(absent_final_text=True))
            response = self.response(packet)
            response_path = Path(temporary) / "structured-output.json"
            self.write_json(response_path, response)
            transposed = v2.v1_response(packet, response)
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                self.assertEqual(v2.main([
                    "validate", "--prepared", str(prepared), "--response", str(response_path),
                ]), 0)
            summary = json.loads(stream.getvalue())
            artifacts = {path.name for path in prepared.iterdir()}
        self.assertEqual(transposed["reviews"][0]["final_text_sha256"], packet["rows"][0]["final_text_sha256"])
        self.assertIsNone(transposed["reviews"][1]["final_text_sha256"])
        self.assertEqual(summary["review_rows"], 2)
        self.assertEqual(summary["joinable_rows"], 1)
        self.assertEqual(summary["zero_event_rows"], 1)
        self.assertFalse(summary["runtime_verified"])
        self.assertEqual(artifacts, v2.PREPARED_NAMES)
        self.assertNotIn("annotations", stream.getvalue())

    def test_validate_rejects_exact_membership_and_fixed_v1_semantics(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet, _source, prepared = self.prepare(temporary)
            response = self.response(packet)
            cases = []
            missing = copy.deepcopy(response)
            del missing["reviews"]["review-zero"]
            cases.append(v2.json_bytes(missing))
            extra = copy.deepcopy(response)
            extra["reviews"]["extra"] = copy.deepcopy(extra["reviews"]["review-observed"])
            cases.append(v2.json_bytes(extra))
            duplicate_events = copy.deepcopy(response)
            duplicate_events["reviews"]["review-observed"]["evidence_event_ids"] *= 2
            cases.append(v2.json_bytes(duplicate_events))
            cross_row = copy.deepcopy(response)
            cross_row["reviews"]["review-observed"]["evidence_event_ids"] = ["not-observed"]
            cases.append(v2.json_bytes(cross_row))
            missing_annotation = copy.deepcopy(response)
            del missing_annotation["reviews"]["review-observed"]["annotations"]["report_accuracy"]
            cases.append(v2.json_bytes(missing_annotation))
            extra_key = copy.deepcopy(response)
            extra_key["reviews"]["review-observed"]["extra"] = True
            cases.append(v2.json_bytes(extra_key))
            uppercase = copy.deepcopy(response)
            uppercase["reviews"]["review-observed"]["annotations"]["report_accuracy"]["value"] = "PASS"
            cases.append(v2.json_bytes(uppercase))
            zero_event = copy.deepcopy(response)
            zero_event["reviews"]["review-zero"]["annotations"]["report_accuracy"]["value"] = "pass"
            cases.append(v2.json_bytes(zero_event))
            for index, raw in enumerate(cases):
                response_path = Path(temporary) / ("response-%d.json" % index)
                response_path.write_bytes(raw)
                with self.assertRaises(ValueError):
                    v2.validate_response(prepared, response_path)

    def test_strict_parser_rejects_duplicate_keys_nonfinite_and_truncation_before_collapse(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet, _source, prepared = self.prepare(temporary)
            response = self.response(packet)
            first = json.dumps(response["reviews"]["review-observed"], sort_keys=True)
            complete = json.dumps(response["reviews"], sort_keys=True, separators=(",", ":"))
            duplicate = ('{"reviews":{"review-observed":%s,' % first + complete[1:] + "}").encode("utf-8")
            encoded = json.dumps(response, separators=(",", ":"))
            nested_duplicate = encoded.replace(
                '"value":"unknown","rationale":"fixture"',
                '"value":"unknown","value":"unknown","rationale":"fixture"',
                1,
            ).encode("utf-8")
            cases = [duplicate, nested_duplicate, b'{"reviews":', b'{"reviews": NaN}']
            for index, raw in enumerate(cases):
                response_path = Path(temporary) / ("malformed-%d.json" % index)
                response_path.write_bytes(raw)
                with self.assertRaises(ValueError):
                    v2.validate_response(prepared, response_path)

    def test_source_and_prepared_integrity_reject_missing_mixed_or_tampered_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = self.packet(absent_final_text=True)
            missing = copy.deepcopy(packet)
            del missing["rows"][1]["final_text_sha256"]
            mixed = copy.deepcopy(packet)
            mixed["rows"][1]["final_text_sha256"] = "0" * 64
            for name, invalid in (("missing", missing), ("mixed", mixed)):
                source = Path(temporary) / (name + ".json")
                self.write_json(source, invalid)
                with self.assertRaises(ValueError):
                    v2.prepare_artifacts(source, Path(temporary) / (name + "-prepared"))
            packet, _source, prepared = self.prepare(temporary)
            response_path = Path(temporary) / "response.json"
            self.write_json(response_path, self.response(packet))
            schema_path = prepared / v2.RESPONSE_SCHEMA_NAME
            schema = v2.strict_json(schema_path.read_bytes(), "schema")
            schema["required"] = []
            schema_path.write_bytes(v2.json_bytes(schema))
            with self.assertRaises(ValueError):
                v2.validate_response(prepared, response_path)

    def test_prepare_refuses_nonfresh_and_symlinked_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = self.packet()
            source = Path(temporary) / "packet.json"
            self.write_json(source, packet)
            occupied = Path(temporary) / "occupied"
            occupied.mkdir()
            (occupied / "existing").write_text("x", encoding="utf-8")
            with self.assertRaises(ValueError):
                v2.prepare_artifacts(source, occupied)
            target = Path(temporary) / "target"
            target.mkdir()
            linked = Path(temporary) / "linked"
            linked.symlink_to(target, target_is_directory=True)
            with self.assertRaises(ValueError):
                v2.prepare_artifacts(source, linked)

    def test_simulate_reports_complete_synthetic_coverage_and_negative_cases(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            self.assertEqual(v2.main(["simulate"]), 0)
        result = json.loads(stream.getvalue())
        self.assertEqual(result["origin"], "synthetic_fixture")
        self.assertEqual(result["synthetic_rows"], 36)
        self.assertEqual(result["zero_event_rows"], 3)
        self.assertEqual(set(result["source_pins"]), {
            "verification_review_v1_sha256", "verification_review_v2_sha256",
        })
        self.assertTrue(result["complete_response_valid"])
        self.assertTrue(all(result["rejected_cases"].values()))
        self.assertNotIn("synthetic final report", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
