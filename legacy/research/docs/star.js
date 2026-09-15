// The star button's count, on every page of this site.
//
// Starring a repository needs a signed-in GitHub session and a write to GitHub's API, which a
// static page cannot do without a backend or a third-party widget. The button is therefore a
// link to the repository, and this script only reads the number next to it from GitHub's public
// repository endpoint: one unauthenticated GET, no cookies, nothing stored, and no number shown
// when the request fails or the rate limit is reached.
//
// It is deliberately separate from compare.js: that file is the comparison engine and its page
// behaviour, this one is the only code on the site that talks to another host.

(function () {
  "use strict";

  var STARS_URL = "https://api.github.com/repos/purpleeddy/agents-md-lab";
  // GitHub needs a moment to count a star the visitor has just given, and a visitor who leaves
  // and returns repeatedly must not spend the hourly limit of the address they share.
  var AFTER_RETURN_MS = 2000;
  var MIN_INTERVAL_MS = 60000;

  var count = document.getElementById("star-count");
  var last = 0;

  function read() {
    last = Date.now();
    fetch(STARS_URL).then(function (response) {
      if (!response.ok) {
        throw new Error("stars: " + response.status);
      }
      return response.json();
    }).then(function (repo) {
      if (typeof repo.stargazers_count !== "number") {
        return;
      }
      var stars = repo.stargazers_count + "";
      if (count.textContent && count.textContent !== stars) {
        count.classList.add("bumped");
        setTimeout(function () { count.classList.remove("bumped"); }, 200);
      }
      count.textContent = stars;
    }, function () {
      // Offline, refused or rate limited: the button stays a link with no number.
    });
  }

  if (!count) {
    return;
  }
  read();
  document.addEventListener("visibilitychange", function () {
    if (document.hidden || Date.now() - last < MIN_INTERVAL_MS) {
      return;
    }
    setTimeout(read, AFTER_RETURN_MS);
  });
})();
