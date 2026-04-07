import os

css_to_append = r'''
/* --- SIDEBAR & EYE PROTECTION FIXES --- */
.sidebar-section { margin-bottom: 2rem; }
.sidebar-section__title { color: var(--text-secondary); font-size: 0.75rem; font-weight: 800; letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 1rem; }
.sidebar-nav { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.35rem; }
.sidebar-nav__link { display: flex; align-items: flex-start; gap: 0.85rem; padding: 0.85rem 1rem; border-radius: var(--radius-sm); color: var(--text-secondary); transition: background var(--transition-base), color var(--transition-base), transform var(--transition-base), border var(--transition-base); border: 1px solid transparent; }
.sidebar-nav__link:hover { color: var(--text-primary); background: var(--muted-surface); transform: translateX(4px); }
.sidebar-nav__link.is-active { color: var(--text-primary); background: var(--accent-gradient-soft); border-color: var(--glass-border-soft); box-shadow: inset 0 0 0 1px rgba(255,255,255,0.04); }
.sidebar-nav__icon { width: 1.8rem; height: 1.8rem; flex-shrink: 0; display: inline-flex; align-items: center; justify-content: center; border-radius: 0.5rem; background: var(--muted-surface); color: inherit; transition: background var(--transition-base); }
.sidebar-nav__link.is-active .sidebar-nav__icon { background: var(--accent-gradient); color: #fff; box-shadow: var(--hero-glow); }
.sidebar-nav__copy { display: flex; flex-direction: column; gap: 0.15rem; }
.sidebar-nav__copy strong { font-size: 0.95rem; font-weight: 700; }
.sidebar-nav__copy span { font-size: 0.8rem; color: var(--text-secondary); opacity: 0.8; }
.sidebar-install { margin-top: 2rem; padding-top: 2rem; border-top: 1px solid var(--table-border); display: grid; gap: 0.75rem; }
.sidebar-install__button { width: 100%; display: flex; align-items: center; justify-content: center; gap: 0.5rem; padding: 0.75rem; border-radius: var(--radius-pill); border: 1px solid var(--glass-border); background: var(--glass-fill); color: var(--text-primary); font-weight: 700; transition: all var(--transition-base); }
.sidebar-install__button:hover { background: var(--accent-gradient-soft); transform: translateY(-2px); border-color: var(--glass-border-strong); }
.sidebar-install__note { font-size: 0.76rem; color: var(--text-secondary); text-align: center; }

html[data-eye-protection="on"] body::after {
    content: ""; position: fixed; inset: 0; background: rgba(255, 170, 0, 0.14);
    pointer-events: none; z-index: 99999; mix-blend-mode: multiply;
}
html[data-eye-protection="on"][data-theme="clean"] body::after {
    mix-blend-mode: color-burn; background: rgba(255, 150, 0, 0.1);
}
'''
with open(r'C:\Users\ASUS\Documents\Tech Elecon Pvt. Ltd\Project\SmartRecruit\1_Web_Portal_Django\smartrecruit_project\static\css\styles.css', 'a', encoding='utf-8') as f:
    f.write('\n' + css_to_append)
