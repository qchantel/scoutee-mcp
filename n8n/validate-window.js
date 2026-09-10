// n8n Code node, run once for all input items. This source is inserted by the artifact generator.
const pages = $input.all().map((item) => item.json);
if (!pages.length) throw new Error('No pages returned; keep the existing checkpoint.');
const first = pages[0];
if (first.total > first.pages * first.page_size || pages.length !== first.pages) {
  throw new Error('Window exceeds the plan page cap. Narrow the time window; do not advance the checkpoint.');
}
const unique = new Map();
for (let index = 0; index < pages.length; index++) {
  const page = pages[index];
  if (page.page !== index + 1 || page.total !== first.total || page.pages !== first.pages) {
    throw new Error('Pagination changed during the run. Retry the same time window.');
  }
  for (const notice of page.items) {
    if (unique.has(notice.id)) throw new Error('Duplicate page: retry without moving the checkpoint.');
    unique.set(notice.id, notice);
  }
}
if (unique.size !== first.total) throw new Error('Incomplete window; keep the checkpoint.');
return [{json: {items: [...unique.values()], window: $('Prepare window').first().json, delivery_confirmed: false}}];
