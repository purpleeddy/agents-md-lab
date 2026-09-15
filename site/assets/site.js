/* The page remains readable and downloadable when scripting is unavailable. */
(() => {
  const page = document.body;
  for (const button of document.querySelectorAll('[data-copy]')) {
    button.hidden = false;
    button.addEventListener('click', async () => {
      const section = button.closest('.actions').parentElement;
      const status = section.querySelector('[data-copy-status]');
      const fallback = section.querySelector('[data-copy-fallback]');
      const source = fallback.querySelector('textarea');
      try {
        await navigator.clipboard.writeText(source.value);
        fallback.hidden = true;
        status.textContent = page.dataset.copySuccess;
      } catch {
        status.textContent = page.dataset.copyFailure;
        fallback.hidden = false;
        source.focus();
        source.select();
      }
    });
  }
  const locale = document.querySelector('[data-locale-switch]');
  const updateLocaleAnchor = () => {
    if (!locale) return;
    const destination = new URL(locale.href);
    destination.hash = location.hash;
    locale.href = destination.href;
  };
  updateLocaleAnchor();
  window.addEventListener('hashchange', updateLocaleAnchor);
})();
