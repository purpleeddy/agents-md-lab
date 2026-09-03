// Evaluation engine for AGENTS.md / CLAUDE.md files, in the browser and in Node.
//
// The same criteria file (docs/criteria.json) drives this engine and scripts/compare.py, and
// tests/test_compare.py proves that the two produce identical verdicts. Keep every change in
// step with the Python engine: the regexes come from the JSON, and the only logic here is how
// lines are split, counted and combined.
//
// No `u` flag on any RegExp: the Python side compiles with re.ASCII, and an unflagged
// JavaScript RegExp is the ASCII dialect that matches it.

(function (root) {
  "use strict";

  var MAX_EVIDENCE = 3;

  function normalize(text) {
    return text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  }

  function splitLines(text) {
    return normalize(text).split("\n");
  }

  function countLines(text) {
    // Newline-terminated lines, the same number `wc -l` prints.
    var count = 0;
    var normalized = normalize(text);
    for (var i = 0; i < normalized.length; i += 1) {
      if (normalized.charAt(i) === "\n") {
        count += 1;
      }
    }
    return count;
  }

  function compilePattern(pattern, flags) {
    var jsFlags = "";
    if (flags.indexOf("i") !== -1) {
      jsFlags += "i";
    }
    if (flags.indexOf("m") !== -1) {
      jsFlags += "m";
    }
    return new RegExp(pattern, jsFlags);
  }

  function matchingLines(lines, regex) {
    var hits = [];
    for (var i = 0; i < lines.length; i += 1) {
      if (regex.test(lines[i])) {
        hits.push({ line: i + 1, text: lines[i] });
      }
    }
    return hits;
  }

  function evidenceFrom(hits) {
    return hits.slice(0, MAX_EVIDENCE).map(function (hit) {
      return { line: hit.line, text: hit.text };
    });
  }

  function evaluateRegexRule(lines, pattern, flags, passIf) {
    var hits = matchingLines(lines, compilePattern(pattern, flags));
    if (passIf === "match") {
      return { pass: hits.length > 0, evidence: evidenceFrom(hits) };
    }
    if (passIf === "no_match") {
      return { pass: hits.length === 0, evidence: evidenceFrom(hits) };
    }
    throw new Error("unknown pass_if for a regex rule: " + passIf);
  }

  function evaluateCriterion(criterion, text, lines) {
    var i;
    if (criterion.kind === "lines") {
      var total = countLines(text);
      return { pass: total <= criterion.pass_if.max_lines, evidence: [], lines: total };
    }
    if (criterion.kind === "regex") {
      return evaluateRegexRule(lines, criterion.pattern, criterion.flags, criterion.pass_if);
    }
    if (criterion.kind === "emphasis") {
      var regex = compilePattern(criterion.pattern, criterion.flags);
      var nonempty = [];
      for (i = 0; i < lines.length; i += 1) {
        if (lines[i].trim() !== "") {
          nonempty.push({ line: i + 1, text: lines[i] });
        }
      }
      var hits = nonempty.filter(function (entry) {
        return regex.test(entry.text);
      });
      var limit = Math.round(criterion.pass_if.max_ratio * 1000);
      return {
        pass: hits.length * 1000 <= limit * nonempty.length,
        evidence: evidenceFrom(hits),
        emphatic_lines: hits.length,
        nonempty_lines: nonempty.length
      };
    }
    if (criterion.kind === "composite") {
      if (criterion.combine !== "any") {
        throw new Error("unknown combine: " + criterion.combine);
      }
      var results = criterion.rules.map(function (rule) {
        return evaluateRegexRule(lines, rule.pattern, rule.flags, rule.pass_if);
      });
      var passed = false;
      var evidence = [];
      for (i = 0; i < results.length; i += 1) {
        if (results[i].pass) {
          passed = true;
          evidence = results[i].evidence;
          break;
        }
      }
      if (!passed) {
        for (i = 0; i < results.length; i += 1) {
          evidence = evidence.concat(results[i].evidence);
        }
        evidence = evidence.slice(0, MAX_EVIDENCE);
      }
      return {
        pass: passed,
        evidence: evidence,
        rules: results.map(function (result) {
          return result.pass;
        })
      };
    }
    throw new Error("unknown criterion kind: " + criterion.kind);
  }

  // {criterion id: verdict} for one file. `filename` is accepted for parity with the Python
  // engine and is not read by any criterion in version 1.0.
  function evaluate(text, filename, criteria) {
    var lines = splitLines(text);
    var verdicts = {};
    criteria.criteria.forEach(function (criterion) {
      verdicts[criterion.id] = evaluateCriterion(criterion, text, lines);
    });
    return verdicts;
  }

  function coverage(verdicts) {
    return Object.keys(verdicts).filter(function (id) {
      return verdicts[id].pass;
    }).length;
  }

  var api = {
    evaluate: evaluate,
    coverage: coverage,
    countLines: countLines,
    splitLines: splitLines
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  root.AgentsMdLab = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
