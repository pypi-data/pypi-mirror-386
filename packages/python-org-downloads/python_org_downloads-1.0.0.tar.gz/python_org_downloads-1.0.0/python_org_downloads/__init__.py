"""Access python.org download artifacts programmatically
Offers some functionality to generate indexes of releases and release artifacts. It also provides the capability of retrieving (downloading) the identified artifacts.
"""

from importlib.resources import as_file as resource_file, files as resource_files
from json import load as json_load
from logging import getLogger
from pathlib import Path, PurePosixPath
from re import compile as re_compile, match as re_match
from sys import modules as sys_modules
from tempfile import mkdtemp

# from bs4 import BeautifulSoup
import bs4
from requests import get as requests_get
from rich.console import Console
from rich.table import Table

DATA_DIRECTORY_NAME = 'data'
LOGGER = getLogger(__name__)

__version__ = '1.0.0'

def load_artifacts_kb(original_class, kb_file_name='artifacts_kb.json'):
	"""Decorator for PythonOrgArtifact
	It loads the KNOWLEDGE_BASE from a JSON data file into the class. Used to decouple all that static logic from the python code.

	:param original_class: the class to decorate (should probably be PythonOrgArtifact)
	:type original_class: type
	:param kb_file_name: the file name inside the data directory to load the information from
	:type kb_file_name: str
	:return: the updated class
	:rtype: type
	"""

	data_dir = resource_files(sys_modules[__name__]) / DATA_DIRECTORY_NAME
	with resource_file(data_dir / kb_file_name) as knowledge_base:
		original_class.KNOWLEDGE_BASE = json_load(knowledge_base.open('rt'))

	for artifact_type in original_class.KNOWLEDGE_BASE:
		pattern = eval("rf'''" + original_class.KNOWLEDGE_BASE[artifact_type]['pattern_fstring'] + "'''", None, original_class.KNOWLEDGE_BASE[artifact_type].get('map', {}))
		original_class.KNOWLEDGE_BASE[artifact_type]['pattern'] = re_compile(pattern)

	return original_class


def update_artifact_version_extensions(original_class):
	"""Decorator for NormalizedPythonVersion
	Uses the _RELEASE_FILE_REGEXP_TEMPLATE attribute and the PythonOrgArtifact.KNOWLEDGE_BASE data to generate the RELEASE_FILE_REGEXP attribute.

	At this point is just compiling all the possible file name extensions of CPython release artifacts.

	:param original_class: the class to decorate (should probably be NormalizedPythonVersion)
	:type original_class: type
	:return: the updated class
	:rtype: type
	"""

	extensions = set()
	for artifact_type, format_details in PythonOrgArtifact.KNOWLEDGE_BASE.items():
		if 'map' in format_details:
			for extension in format_details['map'].get('format', {}).keys():
				extensions.add(extension)
	original_class.RELEASE_FILE_REGEXP = original_class._RELEASE_FILE_REGEXP_TEMPLATE.format(extensions='|'.join((key.replace('.', r'\.') for key in extensions)))
	return original_class


class InvalidVersionStringError(ValueError):
	"""
	The provided string is not a valid CPython artifact name.
	"""


@load_artifacts_kb
class PythonOrgArtifact(PurePosixPath):
	"""A python.org release artifact
	Describes a release artifact and provides some helper methods for them. The base "identifier" is the artifact path/name, inheriting from PurePosixPath which provides a lot of extra functionality.
	"""

	related = None

	def __init__(self, path, parent_path=None):
		"""Magic initialization
		Detects the version and the format.

		:param path: the path/name of the artifact
		:type path: PathLike
		:param parent_path: adds the provided value to "path" when storing it as an attribute
		:type parent_path: PathLike|None
		"""

		version, extra = NormalizedPythonVersion.from_distribution_file(path, parent_path=parent_path)
		super().__init__(version.path)
		self.release_version = version
		self.release_type, self.release_format = self.detect_format(extra)

	@classmethod
	def detect_format(cls, extra):
		"""Detect the artifact format
		Leverages the KNOWLEDGE_BASE to identify the type and format of the artifact.

		:param extra: the extra content left after detecting/parsing the CPython release file name
		:type extra: str
		:return: the type and format of the artifact
		:rtype: tuple[str, dict]
		:raises: ValueError if the format is not found in the KNOWLEDGE_BASE patterns
		"""

		for artifact_type, type_details in cls.KNOWLEDGE_BASE.items():
			matched_format = re_match(type_details['pattern'], extra)
			if matched_format is not None:
				artifact_format = {}
				for key, value in matched_format.groupdict().items():
					if value is not None:
						artifact_format[key] = value
					elif ('pattern_defaults' in type_details) and (key in type_details['pattern_defaults']):
						artifact_format[key] = type_details['pattern_defaults'][key]
				if 'map' in type_details:
					for key in artifact_format:
						if key in type_details['map']:
							artifact_format[key] = type_details['map'][key][artifact_format[key]]
				return artifact_type, artifact_format

		raise ValueError(f'Unknown artifact format: {extra}')

	def detect_related_from_links(self, links_in_dir):
		"""Detect files related to this artifact
		Some extra files are provided by the repo, mostly about signing and confirming the integrity of the artifacts

		:param links_in_dir: all the links found in the artifact's parent directory
		:type links_in_dir: list[str]
		:return: Nothing, it updates the object in place
		:rtype: None
		"""

		self.related = [a_link[len(self.name):].rstrip('/') for a_link in links_in_dir if a_link.startswith(self.name + '.')]

	@property
	def is_final(self):
		"""Is it a final release?
		Checks the version to see if it's a final release or not.

		:return: True if it's a final release; otherwise False
		:rtype: bool
		"""

		if hasattr(self.release_version, 'releaselevel'):
			return self.release_version.releaselevel == self.release_version.RELEASELEVEL_MAP[None]

		return False


@update_artifact_version_extensions
class NormalizedPythonVersion(tuple):
	"""A normalized Python version
	It could be either a 3-item tuple (major, minor, micro) or a 5-item tuple (major, minor, micro, releaselevel, serial). It will add the "path" attribute if provided (or set it to None).
	"""

	RELEASE_DIRECTORY_REGEXP = r'^(?P<major>\d+)\.(?P<minor>\d+)(?:\.(?P<micro>\d+))?/$'
	RELEASELEVEL_MAP = {
		'a': 'alpha',
		'b': 'beta',
		'c': 'candidate',
		'rc': 'candidate',
		None: 'final',
	}
	_RELEASE_FILE_REGEXP_TEMPLATE = r'^(P|p)ython-?(?P<major>\d+)\.(?P<minor>\d+)(?:\.(?P<micro>\d+))?(:?(?P<releaselevel>([^\W\d_]|rc))(?P<serial>\d+))?(?P<extra>.*\.({extensions}))$'

	def __new__(cls, major, minor, micro=0, releaselevel=None, serial=None, path=None):
		"""Magic initialization
		It creates a 3-item or 5-item instance depending on the provided parameters

		:param major: the major version number
		:type major: int
		:param minor: the minor version number
		:type minor: int
		:param micro: the micro version number
		:type micro: int
		:param releaselevel: the release level of the artifact (alpha, beta, candidate, final)
		:type releaselevel: str
		:param serial: a serial for the corresponding release level
		:type serial: int
		:param path: a path pointing to the associated directory or artifact
		:type path: PathLike|None
		:return: the new instance
		:rtype: cls
		"""

		major, minor, micro = int(major), int(minor), int(micro)
		components = [major, minor, micro]
		attrs = {'major': major, 'minor': minor, 'micro': micro}
		if releaselevel is not None:
			if releaselevel not in cls.RELEASELEVEL_MAP.values():
				raise ValueError(f'Invalid release level: {releaselevel}')
			if serial is None:
				raise ValueError('Must provide "serial" with "releaselevel"')
			serial = int(serial)
			components += [releaselevel, serial]
			attrs |= {'releaselevel': releaselevel, 'serial': serial}

		result = super().__new__(cls, components)
		for key, value in attrs.items():
			setattr(result, key, value)
		result.path = path if path is None else PurePosixPath(path)

		return result

	@classmethod
	def from_distribution_directory(cls, distribution_directory, parent_path=None):
		"""Create version from a distribution directory
		A version out of a distribution directory will be a 3-item tuple and the path will be pointing to such directory instead of an artifact.

		:param distribution_directory: the distribution directory to get the version from
		:type distribution_directory: str
		:param parent_path: adds the provided value to "path" when storing it as an attribute
		:type parent_path: PathLike|None
		:return: the new instance
		:rtype: cls
		"""

		matching_directory = re_match(cls.RELEASE_DIRECTORY_REGEXP, distribution_directory)
		if matching_directory is not None:
			re_kwargs = {key: value for key, value in matching_directory.groupdict().items() if value is not None}
			path = distribution_directory if parent_path is None else PurePosixPath(parent_path) / distribution_directory
			return cls(**re_kwargs, path=path)

		raise InvalidVersionStringError(f'Not a valid distribution directory: {distribution_directory}')

	@classmethod
	def from_distribution_file(cls, file_name, parent_path=None):
		"""Create version from a distribution file
		A version out of a distribution file will be a 5-item tuple and the path will be pointing the artifact.

		:param file_name: the distribution file to get the version from
		:type file_name: str
		:param parent_path: adds the provided value to "path" when storing it as an attribute
		:type parent_path: PathLike|None
		:return: the new instance
		:rtype: cls
		"""

		matching_file = re_match(cls.RELEASE_FILE_REGEXP, file_name)
		if matching_file is not None:
			re_kwargs = {key: value for key, value in matching_file.groupdict().items() if value is not None}
			if 'releaselevel' in re_kwargs:
				re_kwargs['releaselevel'] = cls.RELEASELEVEL_MAP[re_kwargs['releaselevel']]
				if re_kwargs['serial'] is None:
					re_kwargs['serial'] = 0
			else:
				re_kwargs['releaselevel'] = cls.RELEASELEVEL_MAP[None]
				re_kwargs['serial'] = 0
			re_kwargs['path'] = file_name if parent_path is None else PurePosixPath(parent_path) / file_name
			extra = re_kwargs.pop('extra')
			return cls(**re_kwargs), extra

		raise InvalidVersionStringError(f'Not a valid distribution file: {file_name}')

	def rebuild_simplified(self):
		"""Rebuild as a 3-item tuple
		Can be leveraged to normalize the versions and become able to compare them

		:return: 3-item instance
		:rtype: NormalizedPythonVersion
		"""

		return type(self)(*self[:3], path=self.path)


class PythonOrgDownloads:
	"""Act on python.org downloads
	Diverse methods to act on the different python.org downloads.
	"""

	BASE_URL = 'https://www.python.org/ftp/python'
	LEGACY_RELEASES_DIRECTORY = 'src/'
	LEGACY_THRESHOLD = (2, 0, 0)

	@classmethod
	def _list_release_directory_versions(cls):
		"""List release directory versions
		Scans the downloads base URL for release directories (basically directories with version numbers).

		:return: the list of release
		:rtype: list[NormalizedPythonVersion]
		"""

		base_url_soup = bs4.BeautifulSoup(requests_get(cls.BASE_URL).text, features='html.parser')
		release_directories = set()
		for a_link in base_url_soup.find_all('a'):
			try:
				detected_version = NormalizedPythonVersion.from_distribution_directory(a_link.attrs['href'])
			except InvalidVersionStringError:
				continue
			else:
				release_directories.add(detected_version)

		release_directories = list(release_directories)
		release_directories.sort()
		return release_directories

	@classmethod
	def _list_release_artifacts_in_directory(cls, relative_path, final_only=False):
		"""List release artifacts in directory
		Scans the provided directory for release artifacts. The path is relative to self.BASE_URL and the artifacts are identified using the patterns on the PythonOrgArtifact.KNOWLEDGE_BASE

		:param relative_path: the parent directory path containing the release artifacts. Should be relative to self.BASE_URL
		:type relative_path: PathLike
		:param final_only: if True, only report versions with artifacts having the final release level; otherwise report every version found
		:type final_only: bool
		:return: the artifacts found based on the parameters provided
		:rtype: list[PythonOrgArtifact]
		"""

		directory_soup = bs4.BeautifulSoup(requests_get('/'.join((cls.BASE_URL, str(relative_path)))).text, features='html.parser')
		release_artifacts = []
		links_in_dir = [a_link.attrs['href'] for a_link in directory_soup.find_all('a')]
		for a_link in links_in_dir:
			try:
				release = PythonOrgArtifact(a_link, parent_path=relative_path)
			except InvalidVersionStringError:
				continue
			else:
				if final_only and not release.is_final:
					continue
				release.detect_related_from_links(links_in_dir)
				release_artifacts.append(release)

		release_artifacts.sort()
		return release_artifacts

	@classmethod
	def latest_version(cls, final_only=True, download_tarball=False):
		"""Gets the latest version
		Will look for the very latest or just for the latest "final" release. It will also download such artifact to the current directory if requested.

		:param final_only: if True, only consider artifacts having the final release level; otherwise consider every artifact found
		:type final_only: bool
		:param download_tarball: if True, trigger "download_release" to retrieve the related artifact with the detected version
		:type download_tarball: bool
		:return: the latest version and potentially the path to the downloaded tarball
		:rtype: NormalizedPythonVersion|tuple[NormalizedPythonVersion, Path]
		"""

		release_dir_versions = cls._list_release_directory_versions()
		current_version = None
		if final_only:
			for i in range(len(release_dir_versions), 0, -1):
				if cls._list_release_artifacts_in_directory(release_dir_versions[i-1].path, final_only=final_only):
					current_version = release_dir_versions[i-1]
					break
		else:
			detected_versions = set()
			version_artifacts = cls._list_release_artifacts_in_directory(release_dir_versions[-1].path, final_only=final_only)
			for version_artifact in version_artifacts:
				detected_versions.add(version_artifact.release_version)
			detected_versions = list(detected_versions)
			detected_versions.sort()
			current_version = detected_versions[-1]

		if not download_tarball:
			return current_version

		kwargs = {
			'major': current_version.major,
			'minor': current_version.minor,
			'micro': current_version.micro,
		}
		if hasattr(current_version, 'release_version'):
			kwargs |= {
				'releaselevel': current_version.releaselevel,
				'serial': current_version.serial,
			}

		return current_version, cls.download_release(**kwargs)

	@classmethod
	def list_all_release_artifacts(cls, final_only=False):
		"""List all release artifacts
		Produce a list with every release artifact in the repository.

		:param final_only: if True, only consider artifacts having the final release level; otherwise consider every artifact found
		:type final_only: bool
		:return: the list of all the applicable artifacts
		:rtype: list[PythonOrgArtifact]
		"""

		release_artifacts = cls._list_release_artifacts_in_directory(cls.LEGACY_RELEASES_DIRECTORY, final_only=final_only)
		for release_dir_version in cls._list_release_directory_versions():
			release_artifacts += cls._list_release_artifacts_in_directory(release_dir_version.path, final_only=final_only)

		release_artifacts.sort()
		return release_artifacts

	@classmethod
	def list_release_versions(cls, final_only=True):
		"""Return the list of versions detected
		Compile a list with all the available versions, reporting them as 3 item tuples.

		:param final_only: if True, only report versions with artifacts having the final release level; otherwise report every version found
		:type final_only: bool
		:return: a list of all the detected versions as 3 item tuples
		:rtype: list[NormalizedPythonVersion]
		"""

		detected_versions = set()
		for legacy_release in cls._list_release_artifacts_in_directory(cls.LEGACY_RELEASES_DIRECTORY, final_only=final_only):
			if final_only:
				detected_versions.add(legacy_release.release_version.rebuild_simplified())
			else:
				detected_versions.add(legacy_release.release_version)

		release_dir_versions = cls._list_release_directory_versions()
		if final_only:
			for i in range(len(release_dir_versions), 0, -1):
				if cls._list_release_artifacts_in_directory(release_dir_versions[i-1].path, final_only=final_only):
					release_dir_versions = release_dir_versions[:i]
					break
			detected_versions |= set(release_dir_versions)
		else:
			for release_dir_version in release_dir_versions:
				for release in cls._list_release_artifacts_in_directory(release_dir_version.path, final_only=final_only):
					detected_versions.add(release.release_version)

		detected_versions = list(detected_versions)
		detected_versions.sort()
		return detected_versions

	@classmethod
	def list_version_artifacts(cls, major, minor, micro=0, final_only=True):
		"""List version artifacts
		Produce a list of artifacts related to the requested version

		:param major: the major version number
		:type major: int
		:param minor: the minor version number
		:type minor: int
		:param micro: the micro version number
		:type micro: int
		:param final_only: if True, only report versions with artifacts having the final release level; otherwise report every version found
		:type final_only: bool
		:return: the list of artifacts related to the provided version
		:rtype: list[PythonOrgArtifact]
		"""

		major, minor, micro = int(major), int(minor), int(micro)
		target_version = (major, minor, micro)
		if target_version > cls.LEGACY_THRESHOLD:
			release_directories = cls._list_release_directory_versions()
			if target_version not in release_directories:
				raise ValueError(f'Release {target_version} not found')
			target_directory_version = release_directories.pop(release_directories.index(target_version))
			return cls._list_release_artifacts_in_directory(target_directory_version.path, final_only=final_only)
		else:
			matching_artifacts = []
			for legacy_release in cls._list_release_artifacts_in_directory(cls.LEGACY_RELEASES_DIRECTORY, final_only=final_only):
				if legacy_release.release_version.rebuild_simplified() == target_version:
					matching_artifacts.append(legacy_release)
			return matching_artifacts

	@classmethod
	def download_release(cls, major, minor, micro=0, releaselevel='final', serial=0, artifact_type='source-release', artifact_format={'format': 'tarball_lzma'}, stream_chunk_size=1048576, destination_dir='.', overwrite=False):
		"""Download a release artifact
		Use the version aspects to retrieve a limited list using "list_version_artifacts". Then pick the applicable one from there using "artifact_type" and "artifact_format". Use then "download_artifact" with the identified artifact to perform the download.

		:param major: passed as is to the underlying "list_version_artifacts" method
		:type major: int
		:param minor: passed as is to the underlying "list_version_artifacts" method
		:type minor: int
		:param micro: passed as is to the underlying "list_version_artifacts" method
		:type micro: int
		:param releaselevel: the release level to compare the initial list of artifacts against.
		:type releaselevel: str
		:param serial: the serial to compare the initial list of artifacts against.
		:type serial: int
		:param artifact_type: the release artifact type
		:type artifact_type: str
		:param artifact_format: the release artifact format
		:type artifact_format: dict
		:param stream_chunk_size: passed as is to the underlying "download_artifact" method
		:type stream_chunk_size: int
		:param destination_dir: passed as is to the underlying "download_artifact" method
		:type destination_dir: PathLike|None
		:param overwrite: passed as is to the underlying "download_artifact" method
		:type overwrite: bool
		:return: the path to the local file
		:rtype: Path
		"""

		matched_artifact = None
		for version_artifact in cls.list_version_artifacts(major=major, minor=minor, micro=micro, final_only=False):
			if (version_artifact.release_version.releaselevel == releaselevel) and (version_artifact.release_version.serial == serial):
				if (version_artifact.release_type == artifact_type) and (version_artifact.release_format == artifact_format):
					matched_artifact = version_artifact
					break

		if matched_artifact is None:
			raise ValueError(f'No matching artifact found {major}.{minor}.{micro}{releaselevel}{serial}/{artifact_type}/{artifact_format}')

		return cls.download_artifact(matched_artifact, stream_chunk_size=stream_chunk_size, destination_dir=destination_dir, overwrite=overwrite)

	@classmethod
	def download_artifact(cls, artifact, stream_chunk_size=1048576, destination_dir='.', overwrite=False):
		"""Downloads the requested artifact
		Retrieves the requested artifact and stores it in the provided directory.

		:param artifact: the artifact to download
		:type artifact: PythonOrgArtifact
		:param stream_chunk_size: the size of the "buffer" for the copying process
		:type stream_chunk_size: int
		:param destination_dir: the directory to store the downloaded artifact. If None, it will store it on a temp directory (created using mkdtemp)
		:type destination_dir: PathLike|None
		:param overwrite: if False and a file already exists, it will return the path to such file without doing much else.
		:type overwrite: bool
		:return: the Path object pointing to the downloaded artifact
		:rtype: Path
		"""

		if destination_dir is None:
			destination_dir = mkdtemp()
		destination_dir = Path(destination_dir)
		destination_dir.mkdir(parents=True, exist_ok=True)

		local_file = destination_dir / artifact.name
		if local_file.exists() and not overwrite:
			return local_file
		local_file.unlink(missing_ok=True)

		download_url = '/'.join((cls.BASE_URL, str(artifact)))
		with requests_get(download_url, stream=True) as source_file:
			source_file.raise_for_status()
			with local_file.open('wb') as file_obj:
				for chunk in source_file.iter_content(chunk_size=stream_chunk_size):
					file_obj.write(chunk)

		return local_file

	@classmethod
	def report_all_release_artifacts(cls, final_only=False):
		"""Report all release artifacts
		Print a fancy report (a table) in the command line containing the list of all the release artifacts.

		:param final_only: if True, only report versions with artifacts having the final release level; otherwise report every version found
		:type final_only: bool
		:return: Nothing
		:rtype: str
		"""

		console = Console()

		table = Table(show_header=True, header_style="bold")
		table.add_column("Version")
		table.add_column("Type")
		table.add_column("Format")
		table.add_column("Path", style="dim")

		for release_artifact in cls.list_all_release_artifacts(final_only=final_only):
			table.add_row(str(release_artifact.release_version), release_artifact.release_type, str(release_artifact.release_format), str(release_artifact))

		console.print(table)
		return ''

	@classmethod
	def report_version_artifacts(cls, major, minor, micro=0):
		"""Report version artifacts
		Print a fancy report (a table) in the command line containing the list of all the release artifacts related to the provided version.

		:param major: passed as is to the underlying "list_version_artifacts" method
		:type major: int
		:param minor: passed as is to the underlying "list_version_artifacts" method
		:type minor: int
		:param micro: passed as is to the underlying "list_version_artifacts" method
		:type micro: int
		:return: Nothing
		:rtype: str
		"""

		console = Console()

		table = Table(show_header=True, header_style="bold")
		table.add_column("Version")
		table.add_column("Type")
		table.add_column("Format")
		table.add_column("Path", style="dim")

		for version_artifact in cls.list_version_artifacts(major=major, minor=minor, micro=micro, final_only=False):
			table.add_row(str(version_artifact.release_version), version_artifact.release_type, str(version_artifact.release_format), str(version_artifact))

		console.print(table)
		return ''
