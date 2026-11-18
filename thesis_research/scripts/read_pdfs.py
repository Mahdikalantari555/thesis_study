"""Read PDF text content from deep_researches folder."""
import subprocess, os, sys

pdfs = [
    (r'D:\RS\Thesis\thesis_research\deep_researches\Beyond Attributing S_05851651_20260910_4022202622.pdf', 'Beyond_Attributing_S'),
    (r'D:\RS\Thesis\thesis_research\deep_researches\Beyond Detection_ A _75980825_20260910_3244202644.pdf', 'Beyond_Detection_A'),
]
for p, short_name in pdfs:
    print(f'=== {short_name} ===')
    result = subprocess.run(
        ['python', '-c', 
         'import PyPDF2, sys; r = PyPDF2.PdfReader(sys.argv[1]); t = ""; [t := t + x.extract_text() + "\\n---PAGE---\\n" if x.extract_text() else None for x in r.pages[:5]]; print(t[:2500])'],
        args=[p], capture_output=True, text=True, timeout=20
    )
    print(result.stdout[:2000])
    if result.stderr:
        print('STDERR:', result.stderr[:300])
    print()
