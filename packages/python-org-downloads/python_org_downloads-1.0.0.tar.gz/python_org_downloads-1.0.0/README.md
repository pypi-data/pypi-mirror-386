# python-org-downloads
Programmatically access the artifacts available in the download site at python.org

## PythonOrgDownloads
The main entrypoint would be the `PythonOrgDownloads` class, which contains the helper methods.

### list_release_versions(cls, final_only=True)

Will generate a list with all the versions (3 items tuple version) present on the repository. The `releaselevel` could be anything, so you shouldn't trust this list further than "there is at least 1 release of some kind for each version present". It pulls most of the information from the list of directories on the root, so it's a fairly cheap function.

The `final_only` flag will limit the list to only `final` versions. With this, it will iterate from the bottom up, removing them from the list until it finds a `final` artifact. This raises the cost of the function, since it has to parse at least 1 extra directory and process all its content.

### list_version_artifacts(cls, major, minor, micro=0, final_only=True)

Returns a list of artifacts that match the provided version. With the `final_only` flag the list is limited to artifacts with the `final` release level only.

### download_artifact(cls, artifact, stream_chunk_size=1048576, destination_dir='.', overwrite=False)

Downloads the requested artifact to the provided `destination_dir`. If `destination_dir` is None, then it will download to a temp directory (created using mkdtemp). If `overwrite` is False and a file already exists, it will return the path to such file without doing much else.

The `stream_chunk_size` value is fed to [iter_content (`stream=True`)](https://requests.readthedocs.io/en/latest/api/#requests.Response.iter_content) which can be tweaked to improve the transfer speed and memory consumption.

### download_release(cls, major, minor, micro=0, releaselevel='final', serial=0, artifact_type='source-release', artifact_format={'format': 'tarball_lzma'}, stream_chunk_size=1048576, destination_dir='.', overwrite=False)

Downloads the related artifact to the provided `destination_dir`. The `major`, `minor`, and `micro` parameters are used to get an initial list of artifacts using [list_version_artifacts](#list_version_artifacts). Then the list is further filtered using the `releaselevel`, `serial`, `artifact_type`, and `artifact_format` parameters. The artifact identified at this point is then downloaded using the [download_artifact](#download_artifact) method.

### latest_version(cls, final_only=True, download_tarball=False)

Looks for the highest version available. With the `final_only` flag the search is narrowed down to artifacts with the `final` release level only. If the `download_tarball` flag is provided, then it will download the related tarball using the defaults of the [download_release](#download_release) method

### list_all_release_artifacts(cls, final_only=False)

If you want to know everything that lives in the repo, and you are not worried about spending a couple seconds waiting, you can get the exhaustive list with this method. With the `final_only` flag the search is narrowed down to artifacts with the `final` release level only.

## Command line

You can leverage, up to a point, the integration with [simplifiedapp](https://pypi.org/project/simplifiedapp/) to use some of this from the command line. Assuming that your virtual environment is active you could do:
```
python -m python_org_downloads PythonOrgDownloads list_version_artifacts 3 13 --micro 9
```
You can `python -m python_org_downloads PythonOrgDownloads --help` your way around.

### report_version_artifacts(cls, major, minor, micro=0)

This is a CLI oriented method that works with the results of [list_version_artifacts](#list_version_artifacts) but generates a prettier output, with a table, colors, and stuff.

### report_all_release_artifacts(cls, final_only=False)

Is another CLI oriented method that works with the results of [list_all_release_artifacts](#list_all_release_artifacts) and puts it all in a prettier output, with a table, colors, and stuff.