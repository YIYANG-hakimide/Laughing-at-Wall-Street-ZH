from pathlib import Path
import re
pdf=Path(__file__).resolve().parents[1]/'source.pdf.txt'
text=pdf.read_text(errors='ignore')
expected=['Preface','Introduction','1. "Eeny, Meeny, Miney, Mo"','2. If It\'s Broken, Fix It','3. Nobody Knows Anything','4. Other People\'s Money','5. See It, Believe It!','6. Zero Financial Literacy Required','7. You Know Something They Don\'t','8. You Have People, Too!','9. Fake It Till You Make It!','10. Life with Investor\'s Glasses','11. Success Stories','Appendix','Notes']
for x in expected: print(('FOUND ' if x.lower() in text.lower() else 'MISSING ')+x)
print('pdf_chars',len(text),'pdf_pages_expected',248)
