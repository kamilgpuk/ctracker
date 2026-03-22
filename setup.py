from setuptools import setup

APP = ['app.py']
OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'CFBundleName': 'ctracker',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,
        'NSPrincipalClass': 'NSApplication',
    },
    'packages': ['rumps', 'browser_cookie3', 'curl_cffi'],
    'includes': ['api', '_cffi_backend'],
}

setup(
    app=APP,
    name='ctracker',
    version='1.0.0',
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
