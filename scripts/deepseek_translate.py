import os, json, sys, time, urllib.request
from pathlib import Path
key=os.environ.get('DEEPSEEK_API_KEY')
if not key: raise SystemExit('missing key')
chapter=sys.argv[1]
chunk_size=int(sys.argv[2]) if len(sys.argv)>2 else 8
root=Path(__file__).resolve().parents[1]
book=json.loads((root/'book.json').read_text())
source=next(c for c in book['chapters'] if c['id']==chapter)
blocks=source['blocks']
partial=root/(chapter+'.partial.json')
try: out=json.loads(partial.read_text())
except Exception: out=[]
for start in range(len(out),len(blocks),chunk_size):
 part=blocks[start:start+chunk_size]
 prompt='''你是严谨的中文出版译者。请把下面 JSON 数组中的每个英文段落逐段完整翻译成简体中文，不能摘要、删减、合并、改写或补写。保留数组长度、顺序、标题/正文类型、数字、百分比、金额、日期、引文、脚注标记、公司名和人名。金融术语要准确自然。只输出合法 JSON 数组，每项格式 {"type":"heading"或"text","text":"中文译文"}，不要 Markdown、解释或代码围栏。\n\n原文：\n'''+json.dumps(part,ensure_ascii=False)
 data=json.dumps({'model':os.environ.get('DEEPSEEK_MODEL','deepseek-v4-pro'),'messages':[{'role':'system','content':'你负责完整出版级翻译，绝不省略原文信息。'},{'role':'user','content':prompt}],'temperature':0.1,'max_tokens':12000})
 req=urllib.request.Request('https://api.deepseek.com/chat/completions',data=data.encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 for attempt in range(3):
  try:
   with urllib.request.urlopen(req,timeout=180) as resp: res=json.load(resp)
   content=res['choices'][0]['message']['content'].strip()
   if content.startswith('```'): content=content.split('\n',1)[1].rsplit('```',1)[0].strip()
   got=json.loads(content)
   if len(got)!=len(part): raise ValueError(f'length {len(got)} != {len(part)}')
   out.extend(got); partial.write_text(json.dumps(out,ensure_ascii=False)); print(f'{chapter} {start+1}-{start+len(part)} ok',flush=True); break
  except Exception as e:
   print(f'retry {chapter} {start}: {e}',file=sys.stderr,flush=True); time.sleep(2)
 else: raise SystemExit('failed chunk')
 time.sleep(.5)
md=[]
for b in out:
 md.append(('# ' if b['type']=='heading' else '')+b['text'])
partial.unlink(missing_ok=True)
(root/(chapter+'.zh.md')).write_text('\n\n'.join(md)+'\n')
print('wrote',root/(chapter+'.zh.md'))
