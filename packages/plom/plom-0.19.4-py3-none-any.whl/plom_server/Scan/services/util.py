# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2023-2024 Andrew Rechnitzer

from io import BytesIO
from pathlib import Path
from PIL import Image

from django.core.files import File

from ..models import StagingImage, StagingThumbnail, StagingBundle

from plom.plom_exceptions import PlomBundleLockedException


def check_bundle_object_is_neither_locked_nor_pushed(bundle_obj: StagingBundle) -> None:
    """Raise PlomBundleLockedException exception if bundle is push-locked or pushed."""
    if bundle_obj.is_push_locked:
        raise PlomBundleLockedException("Bundle is push-locked - it cannot be modified")
    if bundle_obj.pushed:
        raise PlomBundleLockedException("Bundle is pushed - it cannot be modified")


def check_any_bundle_push_locked() -> None:
    """Raise PlomBundleLockedException exception when **any** bundle is push-locked."""
    if StagingBundle.objects.filter(is_push_locked=True).exists():
        raise PlomBundleLockedException(
            "Some bundle is push-locked. Please wait for it to finish."
        )


def update_thumbnail_after_rotation(staging_img: StagingImage, angle: int) -> None:
    """Once staging image has been rotated by angle, update the corresponding thumbnail."""
    thumb_obj = staging_img.stagingthumbnail
    thumb_name = Path(thumb_obj.image_file.path).name
    # read in the thumbnail image, rotate it and save to this bytestream
    fh = BytesIO()
    with Image.open(thumb_obj.image_file) as tmp_img:
        tmp_img.rotate(angle, expand=True).save(fh, "png")

    # cannot have new thumbnail and old thumbnail both pointing at the staging image
    # since it is a one-to-one mapping, so delete old before creating (and auto-saving)
    # the new one.
    thumb_obj.delete()
    StagingThumbnail.objects.create(
        staging_image=staging_img, image_file=File(fh, thumb_name)
    )
