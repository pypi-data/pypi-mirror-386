from hashlib import md5
from pathlib import Path

from django.core import serializers

from allure_megauploader.models import UploaderConfigV2


def get_md5_from_value(value: str) -> str:
    return md5(str(value).encode()).hexdigest()


def upload_file_to_system(tmp_filepath: Path, archive_name: str, file) -> Path:
    if not tmp_filepath.exists():
        tmp_filepath.mkdir(exist_ok=True, parents=True)
    filepath = tmp_filepath / archive_name
    with open(filepath, "wb+") as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return filepath


def config_json_snapshot(config: UploaderConfigV2) -> str:
    return serializers.serialize('json', [config], use_natural_foreign_keys=True, indent=4)


def config_from_json_snapshot(json_snapshot: str) -> UploaderConfigV2:
    if json_snapshot:
        config_list = [conf.object for conf in serializers.deserialize('json', json_snapshot)]
        if config_list:
            return config_list[0]
    return None
