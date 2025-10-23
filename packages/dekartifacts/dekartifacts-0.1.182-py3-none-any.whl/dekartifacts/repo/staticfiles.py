import os
from collections import OrderedDict
from dektools.serializer.yaml import yaml
from dektools.file import write_file, sure_dir, clear_dir, split_file, combine_split_files, fetch_split_files
from dektools.fetch import download_content
from dektools.download import download_from_http
from ..artifacts.staticfiles import StaticfilesLocalArtifact, get_artifact_staticfiles_by_url


def create_staticfiles_repo(url_base, repos, limit=None, path_out=None):
    if path_out:
        clear_dir(sure_dir(path_out))
    else:
        path_out = write_file(None)
    index_data = OrderedDict()
    for name, version, url in repos:
        path_target = os.path.join(path_out, name, version)
        filepath = get_artifact_staticfiles_by_url(url)().pull(url)
        target, count = split_file(filepath, limit, clear=True, out=path_target)
        item = os.path.basename(target)
        if name not in index_data:
            index_data[name] = OrderedDict()
        index_data[name][version] = OrderedDict([
            ('url', f"{url_base}/{name}/{version}/{item}"),
            ('origin', None if StaticfilesLocalArtifact.recognize(url) else url)
        ])
    write_file(os.path.join(path_out, 'index.yaml'), s=yaml.dumps(index_data))
    write_file(os.path.join(path_out, 'index.html'), s="""<a href="./index.yaml">index.yaml</a>""")
    return path_out


def fetch_staticfiles_item(url_base, name, version, out=None, username=None, password=None):
    index_content = download_content(f"{url_base}/index.yaml", username=username, password=password)
    index_data = yaml.loads(index_content)
    entry = index_data[name][version]
    return fetch_split_files(entry["url"], out, sername=username, password=password)


def exist_staticfiles_item(url_base, name, version, username=None, password=None):
    index_content = download_content(f"{url_base}/index.yaml", error=True, username=username, password=password)
    if index_content is None:
        return False
    index_data = yaml.loads(index_content)
    if name not in index_data:
        return False
    return version in index_data[name]
