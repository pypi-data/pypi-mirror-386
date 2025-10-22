import os.path
from collections import OrderedDict
from dektools.time import now
from dektools.serializer.yaml import yaml
from dektools.file import write_file, sure_dir, clear_dir
from dektools.zip import compress_files
from dektools.hash import hash_file
from ..artifacts.helm import HelmArtifact, get_artifact_helm_by_url


def create_helm_repo(url_base, repos, path_out=None):
    if path_out:
        clear_dir(sure_dir(path_out))
    else:
        path_out = write_file(None)
    config = OrderedDict([('apiVersion', 'v1'), ('entries', OrderedDict()), ('generated', _now())])
    for repo in repos:
        helm_artifact_cls = get_artifact_helm_by_url(repo)
        helm_artifact = helm_artifact_cls()
        path = helm_artifact.pull(repo)
        meta = HelmArtifact.get_chart_meta(path)
        filename = f"{meta['name']}-{meta['version']}.tgz"
        url = f"{url_base}/{filename}"
        target = os.path.join(path_out, filename)
        compress_files(path, target)
        meta['digest'] = hash_file('sha256', target)
        meta['created'] = _now()
        meta['urls'] = [url]
        config['entries'][meta['name']] = meta
    write_file(os.path.join(path_out, 'index.yaml'), s=yaml.dumps(config))
    write_file(os.path.join(path_out, 'index.html'), s="""<a href="./index.yaml">index.yaml</a>""")
    return path_out


def _now():
    t = now()
    return f"{t.strftime('%Y-%m-%dT%H:%M:%S')}.{t.microsecond:06d}000Z"
