// Evaluation engine for AGENTS.md / CLAUDE.md files, in the browser and in Node.
//
// The same criteria file (docs/criteria.json, whose `sets.rules` and `sets.content` hold the
// two sets) drives this engine and scripts/compare.py, and
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
  // engine and is not read by any criterion in version 1.0.0.
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

// ---------------------------------------------------------------------------
// Page behaviour. Everything below runs only in a browser: tests/parity.js loads this file
// in Node to check the engine above, where there is no document to touch.
// ---------------------------------------------------------------------------

(function (root) {
  "use strict";
  var lab = root.AgentsMdLab;
  var CONDITIONS = ["none", "karpathy", "ours"];
  var criteria = null;
  var contentCriteria = null;
  var comparison = null;

  function esc(value) {
    return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function el(id) {
    return document.getElementById(id);
  }

  function num(value, digits) {
    return Number(value).toFixed(digits === undefined ? 2 : digits);
  }

  // The interval bounds are computed once, in scripts/experiment.py, and only read here.
  function interval(entry) {
    return "[" + num(entry.lo) + ", " + num(entry.hi) + "]";
  }

  function getJSON(path) {
    return fetch(path).then(function (response) {
      if (!response.ok) {
        throw new Error(path + ": " + response.status);
      }
      return response.json();
    });
  }

  // ------------------------------------------------------------------ copy

  function setUpCopy() {
    var button = el("copy-file");
    var template = el("agents-md-text");
    var status = el("copy-status");
    if (!button || !template) {
      return;
    }
    button.addEventListener("click", function () {
      var text = template.content.textContent;
      navigator.clipboard.writeText(text).then(function () {
        status.textContent = "Copied " + lab.countLines(text) + " lines to the clipboard.";
      }, function () {
        status.textContent = "The browser refused the clipboard. Use the download button instead.";
      });
    });
  }

  // ------------------------------------------------------------------ compare table

  function bodyRows(table) {
    return Array.prototype.slice.call(table.tBodies[0].rows).filter(function (row) {
      return row.dataset.key !== undefined;
    });
  }

  function checkedCriteria() {
    return Array.prototype.slice.call(document.querySelectorAll("#matters input:checked"))
      .map(function (input) { return Number(input.value); });
  }

  function applyFilters(table) {
    var wanted = checkedCriteria();
    var type = el("type-filter").value;
    bodyRows(table).forEach(function (row) {
      var bits = row.dataset.c || "";
      var meets = wanted.every(function (index) { return bits.charAt(index) === "1"; });
      var typed = type === "all" || row.dataset.type === type;
      row.classList.toggle("faded", !(meets && typed));
      var evidence = row.nextElementSibling;
      if (evidence && evidence.classList.contains("evidence")) {
        evidence.classList.toggle("faded", !(meets && typed));
      }
    });
  }

  function applySort(table) {
    var how = el("sort-by").value;
    var body = table.tBodies[0];
    var rows = bodyRows(table);
    rows.sort(function (a, b) {
      if (how === "lines") {
        return Number(a.dataset.lines) - Number(b.dataset.lines);
      }
      if (how === "stars") {
        return Number(b.dataset.stars) - Number(a.dataset.stars);
      }
      return a.dataset.key.localeCompare(b.dataset.key);
    });
    rows.forEach(function (row) {
      var evidence = row.nextElementSibling;
      body.appendChild(row);
      if (evidence && evidence.classList.contains("evidence")) {
        body.appendChild(evidence);
      }
    });
  }

  function evidenceList(record) {
    var items = criteria.criteria.map(function (criterion) {
      var verdict = record.criteria[criterion.id];
      var lines = verdict.evidence.map(function (item) {
        var text = item.text === undefined ? "line only: this repository has no license"
          : item.text.trim();
        return '<li><span class="ln">' + item.line + "</span> " + esc(text) + "</li>";
      });
      if (!lines.length) {
        lines = ["<li>no matching line</li>"];
      }
      return "<li><strong>" + esc(criterion.name) + "</strong> — "
        + (verdict.pass ? "met" : "not met") + "<ul>" + lines.join("") + "</ul></li>";
    });
    return "<ul>" + items.join("") + "</ul>";
  }

  function toggleEvidence(table, button) {
    var row = button.closest("tr");
    var open = button.getAttribute("aria-expanded") === "true";
    var next = row.nextElementSibling;
    if (open) {
      button.setAttribute("aria-expanded", "false");
      button.textContent = "+";
      if (next && next.classList.contains("evidence")) {
        next.remove();
      }
      return;
    }
    var record = comparison.files.filter(function (item) {
      return item.key === row.dataset.key;
    })[0];
    if (!record) {
      return;
    }
    var holder = document.createElement("tr");
    holder.className = "evidence";
    var cell = document.createElement("td");
    cell.colSpan = row.cells.length;
    cell.innerHTML = evidenceList(record);
    holder.appendChild(cell);
    row.parentNode.insertBefore(holder, row.nextSibling);
    button.setAttribute("aria-expanded", "true");
    button.textContent = "−";
  }

  function makeRow(table, label, record, className) {
    var row = document.createElement("tr");
    row.className = "pinned " + className;
    var head = document.createElement("th");
    head.scope = "row";
    head.className = "c-file";
    head.textContent = label;
    row.appendChild(head);
    // The four fixed columns take their stacked-view label from the stylesheet, like the
    // rows the renderer writes.
    var cells = [record.type || "—", "—", String(record.lines), record.license || "—"];
    cells.forEach(function (value, index) {
      var cell = document.createElement("td");
      cell.textContent = value;
      if (index === 1 || index === 2) {
        cell.className = "num";
      }
      row.appendChild(cell);
    });
    criteria.criteria.forEach(function (criterion) {
      var verdict = record.criteria[criterion.id];
      var cell = document.createElement("td");
      cell.className = "v " + (verdict.pass ? "met" : "unmet");
      var pill = document.createElement("span");
      pill.className = "pill";
      pill.textContent = verdict.pass ? "met" : "not met";
      cell.appendChild(pill);
      row.appendChild(cell);
    });
    var total = document.createElement("td");
    total.className = "num met-count";
    total.textContent = record.met + "/" + record.of;
    row.appendChild(total);
    return row;
  }

  function setPinnedRow(table, className, row) {
    var existing = table.querySelector("tr." + className);
    if (existing) {
      existing.remove();
    }
    if (row) {
      table.tBodies[0].insertBefore(row, table.tBodies[0].firstChild);
    }
  }

  function buildMattersControls(table) {
    var box = el("matters");
    criteria.criteria.forEach(function (criterion, index) {
      var label = document.createElement("label");
      var input = document.createElement("input");
      input.type = "checkbox";
      input.value = String(index);
      input.addEventListener("change", function () { applyFilters(table); });
      label.appendChild(input);
      label.appendChild(document.createTextNode(" " + criterion.name));
      box.appendChild(label);
    });
  }

  function setUpTable() {
    var table = el("compare-table");
    if (!table) {
      return;
    }
    buildMattersControls(table);
    el("compare-controls").hidden = false;
    el("compare-controls-2").hidden = false;
    el("type-filter").addEventListener("change", function () { applyFilters(table); });
    el("sort-by").addEventListener("change", function () { applySort(table); });
    el("show-ours").addEventListener("change", function (event) {
      if (!comparison) {
        return;
      }
      var record = comparison.ours;
      record.type = "AGENTS.md";
      setPinnedRow(table, "ours-row",
        event.target.checked ? makeRow(table, "this repository, root AGENTS.md", record, "ours-row") : null);
    });
    table.addEventListener("click", function (event) {
      var button = event.target.closest("button.expand");
      if (button && comparison) {
        toggleEvidence(table, button);
      }
    });
  }

  // ------------------------------------------------------------------ content matrix

  // The second criteria set is a plain matrix: the same ten files, the eight content criteria,
  // no filter and no evidence rows. It is built here rather than written into the page because
  // the page has a size budget and the data is already fetched; readers without JavaScript get
  // the link to docs/generated/comparison.md that sits under the table.
  function contentMatrix(files, content) {
    var ids = content.criteria.map(function (criterion) { return criterion.id; });
    var rows = files.map(function (record) {
      var row = ['<a href="' + esc(record.url_view) + '">' + esc(record.repo) + "</a>"];
      ids.forEach(function (id) {
        var pass = record.criteria_content[id].pass;
        row.push('<span class="v ' + (pass ? "met" : "unmet") + '"><span class="pill">'
          + (pass ? "met" : "not met") + "</span></span>");
      });
      row.push(record.met_content + "/" + record.of_content);
      return row;
    });
    var totals = ["Met by"];
    ids.forEach(function (id) {
      totals.push(String(files.filter(function (record) {
        return record.criteria_content[id].pass;
      }).length));
    });
    totals.push("of " + files.length + " files");
    rows.push(totals);
    var headers = ["File"].concat(content.criteria.map(function (criterion) {
      return criterion.name;
    })).concat(["Criteria met"]);
    // The caption swaps with the set: the static table above carries the rule-set sentence.
    return table(headers, rows, "t-wide",
      "Coverage of eight sourced content criteria by ten published instruction files, each "
      + "pinned by commit.");
  }

  function setUpSetSwitch() {
    var select = el("criteria-set");
    var holder = el("content-matrix");
    var wrap = el("compare-table") ? el("compare-table").parentNode : null;
    if (!select || !holder || !wrap || !contentCriteria || !comparison) {
      return;
    }
    el("set-controls").hidden = false;
    select.addEventListener("change", function () {
      var content = select.value === "content";
      if (content && !holder.innerHTML) {
        holder.innerHTML = contentMatrix(comparison.files, contentCriteria);
      }
      holder.hidden = !content;
      wrap.hidden = content;
      el("compare-controls").hidden = content;
      el("compare-controls-2").hidden = content;
    });
  }

  // ------------------------------------------------------------------ check panel

  function verdictItem(criterion, verdict) {
    var detail;
    if (verdict.pass && verdict.evidence.length) {
      detail = 'line ' + verdict.evidence[0].line + ": " + esc(verdict.evidence[0].text.trim());
    } else if (verdict.pass) {
      detail = "no line to quote: this criterion is a count, not a phrase";
    } else {
      detail = "One way to meet it: " + esc(criterion.example);
    }
    return '<li class="' + (verdict.pass ? "met" : "unmet") + '"><span class="mark">'
      + (verdict.pass ? "✓" : "✗") + "</span> " + esc(criterion.name) + " — "
      + (verdict.pass ? "met" : "not met") + '<span class="hint">' + detail + "</span></li>";
  }

  function runCheck() {
    var text = el("check-text").value;
    var name = el("check-name").value || "AGENTS.md";
    var status = el("check-status");
    if (!text.trim()) {
      status.textContent = "Paste a file first.";
      el("check-verdicts").innerHTML = "";
      return;
    }
    var verdicts = lab.evaluate(text, name, criteria);
    var met = lab.coverage(verdicts);
    var items = criteria.criteria.map(function (criterion) {
      return verdictItem(criterion, verdicts[criterion.id]);
    });
    var line = name + ": rule criteria " + met + "/" + criteria.criteria.length;
    if (contentCriteria) {
      var contentVerdicts = lab.evaluate(text, name, contentCriteria);
      line += ", content criteria " + lab.coverage(contentVerdicts) + "/"
        + contentCriteria.criteria.length;
      items.push('<li class="sep">Content criteria: what the file says about the project</li>');
      contentCriteria.criteria.forEach(function (criterion) {
        items.push(verdictItem(criterion, contentVerdicts[criterion.id]));
      });
    }
    status.textContent = line + ".";
    el("check-verdicts").innerHTML = items.join("");
    var table = el("compare-table");
    if (table) {
      setPinnedRow(table, "yours-row", makeRow(table, "yours — " + name, {
        type: name,
        lines: lab.countLines(text),
        license: "—",
        criteria: verdicts,
        met: met,
        of: criteria.criteria.length
      }, "yours-row"));
    }
  }

  function setUpCheck() {
    var button = el("check-run");
    if (!button) {
      return;
    }
    el("check-support").textContent =
      "The check runs the same criteria the table uses, in this page.";
    button.addEventListener("click", runCheck);
  }

  // ------------------------------------------------------------------ experiment

  var PAD = 12, LABEL_W = 300, PLOT_X0 = 312, PLOT_W = 440, ROW_H = 30, HEAD_H = 30;
  var PLOT_X1 = PLOT_X0 + PLOT_W, CHART_W = PLOT_X1 + 60;

  function px(value) {
    return Math.round(value * 10) / 10;
  }

  function metricLabel(metric) {
    return metric.replace(/_/g, " ");
  }

  function cellsN(entry) {
    var values = CONDITIONS.map(function (condition) {
      var cell = entry.cells[condition];
      return cell ? cell.n : 0;
    }).filter(Boolean);
    return values.length ? Math.max.apply(null, values) : 0;
  }

  function dotPlot(task, entry) {
    var metrics = Object.keys(entry.comparison).sort();
    if (!metrics.length) {
      return "";
    }
    var height = HEAD_H + metrics.length * ROW_H + 20;
    var svg = ['<svg class="chart" viewBox="0 0 ' + CHART_W + " " + height
      + '" role="img" aria-label="Proportion of runs meeting each directed metric of '
      + esc(task) + ', by condition, with 95% intervals">'];
    [0, 0.25, 0.5, 0.75, 1].forEach(function (tick) {
      var x = PLOT_X0 + tick * PLOT_W;
      svg.push('<line class="grid" x1="' + x + '" y1="' + (HEAD_H - 8) + '" x2="' + x
        + '" y2="' + (height - 20) + '"/>');
      svg.push('<text x="' + x + '" y="' + (HEAD_H - 14) + '" text-anchor="middle">'
        + tick + "</text>");
    });
    metrics.forEach(function (metric, index) {
      var stats = entry.comparison[metric];
      var y = HEAD_H + index * ROW_H + ROW_H / 2;
      if (index % 2 === 1) {
        svg.push('<rect class="band" x="0" y="' + (HEAD_H + index * ROW_H) + '" width="'
          + CHART_W + '" height="' + ROW_H + '"/>');
      }
      svg.push('<text class="rowlabel" x="' + PAD + '" y="' + (y + 4) + '">'
        + esc(metricLabel(metric)) + "</text>");
      svg.push('<text x="' + (PLOT_X0 - 8) + '" y="' + (y + 4) + '" text-anchor="end">'
        + (stats.direction === "higher" ? "↑ better" : "↓ better") + "</text>");
      CONDITIONS.forEach(function (condition, slot) {
        var cell = stats.conditions[condition];
        if (!cell) {
          return;
        }
        var dy = y + (slot - 1) * 8;
        var x = px(PLOT_X0 + cell.p * PLOT_W);
        svg.push('<line class="bar c-' + condition + '" x1="' + px(PLOT_X0 + cell.lo * PLOT_W)
          + '" y1="' + dy + '" x2="' + px(PLOT_X0 + cell.hi * PLOT_W) + '" y2="' + dy + '"/>');
        svg.push('<circle class="dot c-' + condition + '" cx="' + x + '" cy="' + dy
          + '" r="4"><title>' + condition + " " + cell.k + "/" + cell.n
          + ", 95% interval " + interval(cell) + "</title></circle>");
        if (condition === "ours") {
          svg.push('<text class="rowlabel" x="' + (PLOT_X1 + 8) + '" y="' + (dy + 4) + '">'
            + cell.k + "/" + cell.n + "</text>");
        }
      });
    });
    svg.push("</svg>");
    return svg.join("");
  }

  function legend(n) {
    var items = CONDITIONS.map(function (condition) {
      return '<li><span class="swatch c-' + condition + '"></span>' + condition + "</li>";
    });
    return '<ul class="legend">' + items.join("")
      + '<li><span class="nbadge">n = ' + n + " per cell</span></li></ul>";
  }

  function table(headers, rows, className, caption) {
    var head = headers.map(function (title) {
      return '<th scope="col">' + esc(title) + "</th>";
    }).join("");
    var body = rows.map(function (row) {
      return "<tr>" + row.map(function (cell, index) {
        return index === 0 ? '<th scope="row">' + cell + "</th>" : "<td>" + cell + "</td>";
      }).join("") + "</tr>";
    }).join("");
    return '<div class="tablewrap"><table class="' + (className || "") + '">'
      + (caption ? "<caption>" + esc(caption) + "</caption>" : "")
      + "<thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table></div>";
  }

  function headlineTable(entry) {
    var rows = CONDITIONS.filter(function (condition) {
      return entry.headline[condition];
    }).map(function (condition) {
      var cell = entry.headline[condition];
      return [
        esc(condition),
        cell.pro_up.length ? esc(cell.pro_up.map(metricLabel).join(", ")) : "—",
        cell.con_up.length ? esc(cell.con_up.map(metricLabel).join(", ")) : "—",
        cell.acceptance.k + "/" + cell.acceptance.n,
        String(cell.delivered_runs),
        cell.cost_ratio === null || cell.cost_ratio === undefined
          ? "—" : "×" + num(cell.cost_ratio)
      ];
    });
    return table(["Condition", "Advantages up vs none", "Disadvantages up vs none",
      "Acceptance k/n", "Delivered runs", "Cost ratio vs none"], rows);
  }

  function comparisonTable(entry) {
    var rows = Object.keys(entry.comparison).sort().map(function (metric) {
      var stats = entry.comparison[metric];
      var row = [esc(metricLabel(metric)),
        stats.direction === "higher" ? "↑ better" : "↓ better"];
      CONDITIONS.forEach(function (condition) {
        var cell = stats.conditions[condition];
        row.push(cell ? cell.k + "/" + cell.n + " " + interval(cell) : "—");
      });
      ["karpathy", "ours"].forEach(function (condition) {
        var diff = stats.diff_vs_none[condition];
        row.push(diff ? num(diff.diff) + " " + interval(diff) : "—");
      });
      return row;
    });
    return table(["Metric", "Direction", "none k/n [95% CI]", "karpathy k/n [95% CI]",
      "ours k/n [95% CI]", "karpathy − none [95% CI]", "ours − none [95% CI]"], rows, "t-wide");
  }

  // Cost is rounded to four decimals; turns and duration are printed as the median is, because
  // an even number of runs can put it on a half and rounding it here would disagree with the
  // same number rendered by scripts/compare.py on the findings page.
  var CONTINUOUS = [["total_cost_usd", "cost (USD)", 4], ["num_turns", "turns", null],
    ["duration_ms", "duration (ms)", null]];

  function continuousTable(entry) {
    var rows = CONTINUOUS.map(function (spec) {
      var row = [esc(spec[1]), "↓ better"];
      CONDITIONS.forEach(function (condition) {
        var cell = entry.cells[condition];
        var median = cell && cell.medians ? cell.medians[spec[0]] : undefined;
        var text = median === undefined ? "—"
          : (spec[2] === null ? String(median) : num(median, spec[2]));
        var ratios = entry.cost_ratio_vs_none[condition];
        if (ratios && ratios[spec[0]] && ratios[spec[0]].ratio !== null) {
          text += " (×" + num(ratios[spec[0]].ratio) + ")";
        }
        row.push(text);
      });
      return row;
    });
    return table(["Metric", "Direction", "none median", "karpathy median (ratio)",
      "ours median (ratio)"], rows, "t-wide");
  }

  function renderExperiment(data) {
    var tasks = Object.keys(data.by_task).sort();
    if (!tasks.length) {
      return "";
    }
    var out = ['<p class="footnote">Data generated ' + esc(data.generated_utc)
      + '. Every interval is computed in <code>scripts/experiment.py</code> and read from the '
      + "committed JSON; nothing on this page recomputes one.</p>"];
    tasks.forEach(function (task) {
      var entry = data.by_task[task];
      out.push('<div class="stack-l"><h3>' + esc(task) + "</h3>");
      out.push(headlineTable(entry));
      out.push(comparisonTable(entry));
      out.push(legend(cellsN(entry)));
      out.push(dotPlot(task, entry));
      out.push("<h4>Cost, turns and duration</h4>");
      out.push(continuousTable(entry));
      out.push("</div>");
    });
    return out.join("");
  }

  var ROUND2_LABEL = '<h3>Round 2, <code>ours</code> = v1.2.0, <code>none</code> and '
    + '<code>karpathy</code> reused from the main run</h3>';

  function setUpExperiment() {
    var holder = el("experiment-body");
    if (!holder) {
      return;
    }
    getJSON("data/experiment.json").then(function (data) {
      var html = data && data.by_task ? renderExperiment(data) : "";
      if (!html) {
        return null;
      }
      holder.innerHTML = html;
      // Round 2 is appended after the main run by the same renderer, and fetched second so
      // the order on the page cannot depend on the network.
      return getJSON("data/experiment-round2.json").then(function (round2) {
        var extra = round2 && round2.by_task ? renderExperiment(round2) : "";
        if (extra) {
          holder.insertAdjacentHTML("beforeend", ROUND2_LABEL + extra);
        }
      }, function () {});
    }, function () {
      // The file is not published yet: the pre-registration sentence already in the page stands.
    });
  }

  // ------------------------------------------------------------------ start

  function start() {
    setUpCopy();
    // One fetch: both sets live in docs/criteria.json, so the page cannot end up with one of
    // them and not the other. Without it the check panel keeps the fallback text it ships with,
    // which names the command that does the same job offline.
    getJSON("criteria.json").then(function (loaded) {
      return loaded && loaded.sets ? loaded.sets : null;
    }, function () {
      return null;
    }).then(function (sets) {
      if (!sets) {
        return;
      }
      criteria = sets.rules;
      contentCriteria = sets.content;
      setUpTable();
      setUpCheck();
      return getJSON("data/comparison.json").then(function (data) {
        comparison = data;
        setUpSetSwitch();
      }, function () {
        // Without the data file there are no evidence lines to open, so the row buttons go
        // away rather than sitting there doing nothing.
        comparison = null;
        Array.prototype.forEach.call(document.querySelectorAll("button.expand"), function (b) {
          b.hidden = true;
        });
      });
    });
    setUpExperiment();
  }

  // Exported so tests/test_docs.py can render the experiment section in Node against a
  // recorded run file, where there is no document to attach it to.
  lab.renderExperiment = renderExperiment;
  lab.contentMatrix = contentMatrix;

  if (typeof document === "undefined") {
    return;
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})(typeof globalThis !== "undefined" ? globalThis : this);
