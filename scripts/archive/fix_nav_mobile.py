import os

path = os.path.expanduser('~/jcode-agency/promo-septembre.html')

with open(path) as f:
    content = f.read()

old = '''            .nav-links {
                display: none;
            }'''

new = '''            .nav-links {
                display: flex;
                gap: 0.5rem;
            }

            .nav-links a:not(.lang-btn) {
                display: none;
            }'''

if old not in content:
    print('BLOC NON TROUVE - rien de modifie')
else:
    content = content.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(content)
    print('REMPLACEMENT REUSSI')
