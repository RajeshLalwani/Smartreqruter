import os
import polib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCALE_DIR = os.path.join(BASE_DIR, 'locale')

LANGS = ['en', 'hi', 'es', 'gu']
TRANSLATIONS = {
    'Command': {'en': 'Command', 'hi': 'कमांड', 'es': 'Comando', 'gu': 'આદેશ'},
    'Requisitions': {'en': 'Requisitions', 'hi': 'मांग', 'es': 'Requisiciones', 'gu': 'માંગણીઓ'},
    'Interviews': {'en': 'Interviews', 'hi': 'साक्षात्कार', 'es': 'Entrevistas', 'gu': 'મુલાકાતો'},
    'System': {'en': 'System', 'hi': 'प्रणाली', 'es': 'Sistema', 'gu': 'સિસ્ટમ'},
    'Find Jobs': {'en': 'Find Jobs', 'hi': 'नौकरियां खोजें', 'es': 'Buscar Trabajos', 'gu': 'નોકરીઓ શોધો'},
    'Applications': {'en': 'Applications', 'hi': 'अनुप्रयोग', 'es': 'Aplicaciones', 'gu': 'એપ્લિકેશનો'},
    'My Interviews': {'en': 'My Interviews', 'hi': 'मेरे साक्षात्कार', 'es': 'Mis Entrevistas', 'gu': 'મારી મુલાકાતો'}
}

os.makedirs(LOCALE_DIR, exist_ok=True)

for lang in LANGS:
    lang_dir = os.path.join(LOCALE_DIR, lang, 'LC_MESSAGES')
    os.makedirs(lang_dir, exist_ok=True)
    
    po = polib.POFile()
    po.metadata = {
        'Project-Id-Version': '1.0',
        'Report-Msgid-Bugs-To': 'hr@smartrecruit.ai',
        'POT-Creation-Date': '2026-03-20 02:50+0530',
        'PO-Revision-Date': '2026-03-20 02:50+0530',
        'Last-Translator': 'AI Engine',
        'Language-Team': 'AI Localization',
        'Language': lang,
        'MIME-Version': '1.0',
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Transfer-Encoding': '8bit',
    }
    
    for msgid, translations in TRANSLATIONS.items():
        entry = polib.POEntry(
            msgid=msgid,
            msgstr=translations.get(lang, msgid)
        )
        po.append(entry)
    
    po_path = os.path.join(lang_dir, 'django.po')
    mo_path = os.path.join(lang_dir, 'django.mo')
    
    po.save(po_path)
    po.save_as_mofile(mo_path)
    print(f"Compiled {lang} -> {mo_path}")
