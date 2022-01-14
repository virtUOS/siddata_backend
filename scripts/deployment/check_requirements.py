from os.path import join, isfile, abspath, basename
import importlib
import pkg_resources

from manage import setup_django_dry

COMPARATOR_OPPOSITES = {"<": ">=", "<=": ">", ">": "<=", ">=": "<", "==": "!=", "!=": "=="}
ALL_PKGS = pkg_resources.working_set


def main():
    global logger
    settings, logger = setup_django_dry(logger_name=basename(__file__))

    req_file = abspath(join(settings.BASE_DIR, "..", "requirements.txt"))
    req_dev_file = abspath(join(settings.BASE_DIR, "..", "requirements-dev.txt"))
    errors = test_versions(parse_req_file(req_file, settings))
    errors += test_versions(parse_req_file(req_dev_file, settings))
    if not errors:
        logger.info("All requirements are up-to-date!")
        return 0
    return 1


def test_versions(req_versions):
    errors = []
    dist_infos = {p.key: p for p in ALL_PKGS if p.key in req_versions}
    for reqsource, (reqname, (reqcmp, reqversion)) in req_versions.items():
        display_name = reqname or reqsource
        if reqsource in dist_infos:
            version = dist_infos[reqsource].version
        elif reqname is not None:
            logger.debug(f"Manually importing `{reqname}` to check its version..")
            try:
                pkg = importlib.import_module(reqname)
            except ModuleNotFoundError as e:
                install_cmd = reqsource if "#egg=" in reqsource else (f"{reqsource}{reqcmp}{reqversion}" if reqcmp and reqversion else reqsource)
                logger.error(f"Requirement `{display_name}` not installed!! Install using `pip install {install_cmd}`")
                errors.append(reqsource)
                continue
            else:
                version = get_version(pkg)
        else:
            raise NotImplementedError()
        res = compare_versions(version, reqversion, reqcmp)
        if not res:
            install_cmd = reqsource if "#egg=" in reqsource else (f"{reqsource}{reqcmp}{reqversion}" if reqcmp and reqversion else reqsource)
            logger.error(f"{display_name} should be {reqcmp}{reqversion} but is {version}! Install using `pip install {install_cmd}`")
            errors.append(reqsource)
    return errors

def get_version(pkg):
    if hasattr(pkg, "__version__"):
        return pkg.__version__
    else:
        raise Exception()

def compare_versions(actual, demanded, cmp):
    if demanded is None:
        return True
    if cmp == "=":
        cmp = "=="
    elif cmp in ["~="]:
        raise NotImplementedError()
    return eval(f"packaging.version.parse('{actual}') {cmp} packaging.version.parse('{demanded}')")


def parse_req_file(req_file, settings):
    """returns dict install_name: [import_name, (version_comparator, version)] from req_file"""
    req_dict = {}
    if not isfile(req_file):
        return req_dict
    with open(req_file, "r") as rfile:
        base_lines = []
        for line in rfile.readlines():
            l = line.strip()
            if l and not l.startswith("#"):
                base_lines.append(l[:l.find(" #") if l.find(" #") > 0 else None])
    SEPS = [">=", ">", "<=", "<", "==", "~=", "="] #~=: https://stackoverflow.com/a/39590286/5122790
    for req in base_lines:
        sep = None
        for sep_cand in SEPS:
            if sep_cand in req and not "egg"+sep_cand in req:
                sep = sep_cand
                break
        if "#egg=" in req:
            cmp, version = "=", req.split("#egg=")[0].split("@")[1]
            if version.startswith("v"): version = version[1:]
            pkg_name = req.strip()
            import_name = req.split("#egg=")[1]
        else:
            if sep:
                pkg_name = req.split(sep)[0].strip()
                cmp, version = sep, req.split(sep)[1].strip()
            else:
                pkg_name = req.strip()
                cmp, version = None, None
            import_name = get_import_name(pkg_name, settings)
        req_dict[pkg_name] = (import_name, (cmp, version))
    return req_dict


def get_import_name(req_name, settings):
    """For many importable packages, the name of the package("distribution") and whats imported differs, so we need a function mapping them
    What I call a package often is not a package but a distribution. A distribution can contain zero or more modules or packages"""
    tmp = [p for p in ALL_PKGS if p.key == req_name]
    if len(tmp) == 1:
        #TODO: could use https://stackoverflow.com/a/7184642/5122790 to get the importables from tmp[0].module_path
        #TODO: could use [i for i in iter_modules() if i.name == req_name] to get importables according to https://stackoverflow.com/a/54490088/5122790
        return None #if it's in pkg_resources.working_set then we don't need the import name
    return req_name.replace("-","_")



if __name__ == '__main__':
    main()
