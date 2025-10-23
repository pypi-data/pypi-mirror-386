import os
from collections import OrderedDict
from dektools.serializer.yaml import yaml
from dektools.file import write_file, sure_dir, clear_dir, split_file, combine_split_files
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
        if name not in index_data:
            index_data[name] = OrderedDict()
        index_data[name][version] = OrderedDict([
            ('url', f"{url_base}/{name}/{version}"),
            ('origin', None if StaticfilesLocalArtifact.recognize(url) else url)
        ])
        write_file(os.path.join(path_target, 'index.txt'), s=os.path.basename(target))
    write_file(os.path.join(path_out, 'index.yaml'), s=yaml.dumps(index_data))
    write_file(os.path.join(path_out, 'index.html'), s="""<a href="./index.yaml">index.yaml</a>""")
    return path_out


def fetch_staticfiles_item(url_base, name, version, path_out=None, username=None, password=None):
    def getter(index, n):
        return download_from_http(
            n(f"{url_item}/{item_name}", index), n(os.path.join(path_out, item_name), index),
            username=username, password=password
        )

    if path_out:
        clear_dir(sure_dir(path_out))
    else:
        path_out = write_file(None)
    index_content = download_content(f"{url_base}/index.yaml", username=username, password=password)
    index_data = yaml.loads(index_content)
    url_item = index_data[name][version]["url"]
    item_name = download_content(f"{url_item}/index.txt", username=username, password=password).decode('utf-8')
    return combine_split_files(getter, clear=True, out=path_out)


def exist_staticfiles_item(url_base, name, version, username=None, password=None):
    index_content = download_content(f"{url_base}/index.yaml", error=True, username=username, password=password)
    if index_content is None:
        return False
    index_data = yaml.loads(index_content)
    if name not in index_data:
        return False
    return version in index_data[name]
