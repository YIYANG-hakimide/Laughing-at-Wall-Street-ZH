let book, current = 0;
const $ = s => document.querySelector(s);

fetch('book.json').then(r => r.json()).then(b => {
  book = b;
  buildToc();
  const wanted = location.hash.slice(1);
  const index = book.chapters.findIndex(c => c.id === wanted);
  render(index >= 0 ? index : 0);
}).catch(err => {
  $('#reader').innerHTML = '<p class="error">目录加载失败，请刷新页面重试。</p>';
  console.error(err);
});

window.addEventListener('hashchange', () => {
  if (!book) return;
  const index = book.chapters.findIndex(c => c.id === location.hash.slice(1));
  if (index >= 0 && index !== current) render(index);
});

function buildToc() {
  $('#toc').innerHTML = '';
  book.chapters.forEach((c, i) => {
    const a = document.createElement('a');
    a.href = '#' + c.id;
    a.textContent = zhTitle(c.title, c.id);
    a.onclick = e => {
      e.preventDefault();
      render(i);
      document.querySelector('aside').classList.remove('open');
    };
    a.id = 'toc-' + i;
    $('#toc').append(a);
  });
}

function zhTitle(t, id) {
  const fixed = {Preface: '序言', Intro: '引言', Introduction: '引言', Appendix: '附录', Notes: '注释', Acknowledgments: '致谢'};
  if (fixed[t]) return fixed[t];
  const m = String(t).match(/Chapter\s+(\d+)/i);
  if (m) return '第' + m[1] + '章';
  if (id && /^chapter\d+$/.test(id)) return '第' + id.slice(7) + '章';
  return t;
}

function inline(s) {
  return esc(s)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    .replace(/\*([^*]+?)\*/g, '<em>$1</em>')
    .replace(/_([^_]+?)_/g, '<em>$1</em>');
}

function renderMarkdown(markdown) {
  const lines = markdown.split(/\n/);
  let html = '', tableLines = [], listType = null, listItems = [];
  const flushList = () => {
    if (!listType) return;
    html += '<' + listType + '>' + listItems.join('') + '</' + listType + '>';
    listType = null; listItems = [];
  };
  const flushTable = () => {
    if (!tableLines.length) return;
    const rows = tableLines.map(line => line.trim().split('|').slice(1, -1).map(v => v.trim()));
    const hasHeader = rows.length > 1 && rows[1].every(v => /^[-: ]+$/.test(v));
    const start = hasHeader ? 2 : 0;
    let out = '<table>';
    if (hasHeader) out += '<thead><tr>' + rows[0].map(v => '<th>' + inline(v) + '</th>').join('') + '</tr></thead>';
    out += '<tbody>' + rows.slice(start).map(row => '<tr>' + row.map(v => '<td>' + inline(v) + '</td>').join('') + '</tr>').join('') + '</tbody></table>';
    html += out; tableLines = [];
  };
  const flushBlocks = () => { flushList(); flushTable(); };

  for (const raw of lines) {
    const line = raw.replace(/\u00a0/g, ' ');
    const trimmed = line.trim();
    if (!trimmed) { flushBlocks(); continue; }
    if (/^\|.*\|$/.test(trimmed)) { flushList(); tableLines.push(trimmed); continue; }
    if (/^(---+|\*\s+\*\s+\*)$/.test(trimmed)) { flushBlocks(); html += '<hr>'; continue; }
    const image = trimmed.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
    if (image) { flushBlocks(); const caption = image[1] ? '<figcaption>' + inline(image[1]) + '</figcaption>' : ''; html += '<figure><img src="' + esc(image[2]) + '" alt="' + esc(image[1]) + '">' + caption + '</figure>'; continue; }
    const heading = line.match(/^(#{1,3})\s+(.*)$/);
    if (heading) { flushBlocks(); const tag = heading[1].length === 1 ? 'h2' : heading[1].length === 2 ? 'h3' : 'h4'; html += '<' + tag + '>' + inline(heading[2]) + '</' + tag + '>'; continue; }
    if (line.startsWith('> ')) { flushBlocks(); html += '<blockquote>' + inline(line.slice(2)) + '</blockquote>'; continue; }
    const ordered = trimmed.match(/^\d+[.)]\s+(.*)$/);
    const bullet = trimmed.match(/^(?:[-*•])\s+(.*)$/);
    if (ordered || bullet) {
      const type = ordered ? 'ol' : 'ul';
      if (listType !== type) { flushList(); listType = type; }
      listItems.push('<li>' + inline((ordered || bullet)[1]) + '</li>');
      continue;
    }
    flushBlocks();
    html += '<p>' + inline(line) + '</p>';
  }
  flushBlocks();
  return html;
}

async function render(i) {
  current = i;
  const c = book.chapters[i];
  let translated;
  try {
    const r = await fetch(c.id + '.zh.md', {cache: 'no-store'});
    if (!r.ok) throw new Error(c.id + '.zh.md HTTP ' + r.status);
    translated = await r.text();
  } catch (e) {
    $('#reader').innerHTML = '<p class="error">本章译文加载失败：' + esc(e.message) + '</p>';
    console.error(e);
    return;
  }
  $('#reader').innerHTML = renderMarkdown(translated);
  document.querySelectorAll('nav a').forEach((a, j) => a.classList.toggle('active', j === i));
  $('#progress').textContent = (i + 1) + ' / ' + book.chapters.length;
  if (location.hash !== '#' + c.id) history.replaceState(null, '', '#' + c.id);
  window.scrollTo({top: 0, behavior: 'smooth'});
}

function esc(s) { return String(s).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])); }

$('#prev').onclick = () => render(Math.max(0, current - 1));
$('#next').onclick = () => render(Math.min(book.chapters.length - 1, current + 1));
$('#theme').onclick = () => document.body.classList.toggle('eye');
$('#menu').onclick = () => document.querySelector('aside').classList.toggle('open');
$('#size').oninput = e => $('#reader').style.fontSize = e.target.value + 'px';
