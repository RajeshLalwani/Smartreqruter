import os
import sys

translations = {
    'es': {
        "Command": "Comando",
        "Requisitions": "Requisiciones",
        "Interviews": "Entrevistas",
        "System": "Sistema",
        "Find Jobs": "Buscar Empleos",
        "Applications": "Aplicaciones",
        "My Interviews": "Mis Entrevistas",
        "Neural Chat": "Chat Neuronal",
        "Architecture Design": "Diseño de Arquitectura",
        "Terminate Session": "Terminar Sesión",
        "Send": "Enviar",
        "Save": "Guardar",
        "Submit Code": "Enviar Código",
        "Start Voice Round": "Iniciar Ronda de Voz",
    },
    'hi': {
        "Command": "आदेश",
        "Requisitions": "मांग",
        "Interviews": "साक्षात्कार",
        "System": "प्रणाली",
        "Find Jobs": "नौकरियां खोजें",
        "Applications": "आवेदन",
        "My Interviews": "मेरे साक्षात्कार",
        "Neural Chat": "न्यूरल चैट",
        "Architecture Design": "आर्किटेक्चर डिजाइन",
        "Terminate Session": "सत्र समाप्त करें",
        "Send": "भेजें",
        "Save": "सहेजें",
        "Submit Code": "कोड सबमिट करें",
        "Start Voice Round": "वॉयस राउंड शुरू करें",
    },
    'gu': {
        "Command": "આદેશ",
        "Requisitions": "માંગ",
        "Interviews": "ઇન્ટરવ્યુ",
        "System": "સિસ્ટમ",
        "Find Jobs": "નોકરીઓ શોધો",
        "Applications": "અરજીઓ",
        "My Interviews": "મારા ઇન્ટરવ્યુ",
        "Neural Chat": "ન્યુરલ ચેટ",
        "Architecture Design": "આર્કિટેક્ચર ડિઝાઇન",
        "Terminate Session": "સત્ર સમાપ્ત કરો",
        "Send": "મોકલો",
        "Save": "સાચવો",
        "Submit Code": "કોડ સબમિટ કરો",
        "Start Voice Round": "વોઇસ રાઉન્ડ શરૂ કરો",
    }
}

base_dir = r"c:\Users\ASUS\Documents\Tech Elecon Pvt. Ltd\Project\SmartRecruit\1_Web_Portal_Django\smartrecruit_project\locale"

for lang, trans in translations.items():
    lang_dir = os.path.join(base_dir, lang, 'LC_MESSAGES')
    os.makedirs(lang_dir, exist_ok=True)
    po_file = os.path.join(lang_dir, 'django.po')
    
    with open(po_file, 'w', encoding='utf-8') as f:
        f.write('msgid ""\n')
        f.write('msgstr ""\n')
        f.write('"Content-Type: text/plain; charset=UTF-8\\n"\n\n')
        
        for k, v in trans.items():
            f.write(f'msgid "{k}"\n')
            f.write(f'msgstr "{v}"\n\n')
    
    # Also compile to .mo using msgfmt.py
    os.system(f'python msgfmt.py "{po_file}"')

print("Translations generated and compiled successfully.")
