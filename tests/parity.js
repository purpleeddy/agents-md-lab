// Parity harness: read {"cases": [{"name": ..., "text": ...}, ...]} on stdin, evaluate every
// case with docs/compare.js and print {"name": verdicts} as JSON on stdout. tests/test_compare.py
// compares the result with the Python engine's verdicts on the same cases.
//
// An optional "set" names which set of docs/criteria.json to use; it defaults to "rules". The
// engine reads whichever set it is handed, so the same harness runs the content set.

"use strict";

var fs = require("fs");
var path = require("path");

var root = path.resolve(__dirname, "..");
var engine = require(path.join(root, "docs", "compare.js"));
var input = JSON.parse(fs.readFileSync(0, "utf8"));
var sets = JSON.parse(fs.readFileSync(path.join(root, "docs", "criteria.json"), "utf8")).sets;
var criteria = sets[input.set || "rules"];

var out = {};
input.cases.forEach(function (item) {
  out[item.name] = engine.evaluate(item.text, item.filename || "AGENTS.md", criteria);
});
process.stdout.write(JSON.stringify(out));
