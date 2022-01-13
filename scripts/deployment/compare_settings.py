import importlib.util
from os.path import join, isdir, isfile, abspath, dirname, splitext
import types

base_path = join(dirname(__file__), "..", "..", "siddata_backend", "siddata_backend")
settings_file = join(base_path, "settings.py")
settings_default_file = join(base_path, "settings_default.py")

def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, filename)
    cont = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cont)
    return cont

def compare_settings(print_fn=print, ignore_diffs=None, ignore_toomuch=None):
    ignore_toomuch = ignore_toomuch or {"SIDDATA_SEAFILE_REPOWRITE_PASSWORD", "SIDDATA_SEAFILE_REPOREAD_PASSWORD"}
    ignore_diffs = ignore_diffs or set()
    settings = load_module("settings", settings_file)
    defaults = load_module("settings", settings_default_file)
    new_sets, old_sets, changed_sets = compare_rootsettings(settings, defaults)
    news = [i for i in new_sets if i not in ignore_diffs|ignore_toomuch]
    olds = [i for i in old_sets if i not in ignore_diffs|ignore_toomuch]
    changeds = [i for i in changed_sets if i not in ignore_diffs|ignore_toomuch]
    if news:
        print_fn(f"The following settings are not in your `settings.py`: {news}")
    if olds:
        print_fn(f"The following settings may be too much in your `settings.py`: {olds}")
    if changeds:
        print_fn(f"The following settings differ in your settings and the default: {changeds}")
    compare_installedapps(settings, defaults, print_fn)

def compare_rootsettings(settings, defaults):
    new_sets = {key: val for key, val in defaults.__dict__.items() if key not in settings.__dict__}
    new_sets = {key: val for key, val in new_sets.items() if not isinstance(val, types.ModuleType)} #removes imports
    old_sets = {key: val for key, val in settings.__dict__.items() if key not in defaults.__dict__}
    old_sets = {key: val for key, val in old_sets.items() if not isinstance(val, types.ModuleType)} #removes imports
    sets = {key: val for key, val in settings.__dict__.items() if key in defaults.__dict__}
    changed_sets = {key: (val, defaults.__dict__[key]) for key, val in sets.items() if val != defaults.__dict__[key] and not key.startswith("__") and key not in ["INSTALLED_APPS"]}
    return new_sets, old_sets, changed_sets

def compare_installedapps(settings, defaults, print_fn):
    if set(defaults.INSTALLED_APPS)-set(settings.INSTALLED_APPS):
        print_fn(f"The following INSTALLED_APPS are missing in your config: {set(defaults.INSTALLED_APPS)-set(settings.INSTALLED_APPS)}")
    if set(settings.INSTALLED_APPS)-set(defaults.INSTALLED_APPS):
        print_fn(f"The following INSTALLED_APPS are too much in your config: {set(settings.INSTALLED_APPS)-set(defaults.INSTALLED_APPS)}")



if __name__ == '__main__':
    compare_settings()