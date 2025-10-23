"""A module for augmenting SBOM documents."""

import asyncio
import itertools
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import aiofiles

from mobster.cmd.augment.handlers import CycloneDXVersion1, SPDXVersion2
from mobster.cmd.base import Command
from mobster.error import SBOMError, SBOMVerificationError
from mobster.image import Image, IndexImage
from mobster.oci.artifact import SBOM, SBOMFormat
from mobster.oci.cosign import Cosign, CosignClient, CosignConfig
from mobster.release import (
    Component,
    ReleaseId,
    ReleaseRepository,
    Snapshot,
    make_snapshot,
)

LOGGER = logging.getLogger(__name__)


@dataclass
class SBOMRefDetail:
    """
    Result of SBOM augmentation process.
    The SBOMs are not stored in-memory but in
    the filesystem to ease the load on memory.

    Attributes:
        reference: Reference to the image this attestation belongs to
        sbom_format: The format of the SBOM
        path: Path to the local SBOM file
    """

    reference: str
    sbom_format: SBOMFormat
    path: Path
    attestation_valid: bool


@dataclass
class AugmentConfig:
    """
    Configuration for SBOM augmentation.

    Params:
        cosign: Implementation of the Cosign protocol for manipulating SBOMs
        verify: Use pubkey verification for attestations
        semaphore: asyncio semaphore to limit the number of concurrent operations
        output_dir: Path to directory to save the augmented SBOMs to
        release_id: ReleaseId to optionally inject into SBOMs
    """

    cosign: Cosign
    verify: bool
    semaphore: asyncio.Semaphore
    output_dir: Path
    release_id: ReleaseId | None = None


class AugmentImageCommand(Command):
    """
    Command for augmenting OCI image SBOMs.
    """

    @property
    def name(self) -> str:
        """
        Name of the augment command used for logging purposes.
        """
        return "AugmentImageCommand"

    async def execute(self) -> Any:
        """
        Update OCI image SBOMs based on the supplied args.
        """
        digest = None
        if self.cli_args.reference:
            _, digest = self.cli_args.reference.split("@", 1)

        semaphore = asyncio.Semaphore(self.cli_args.concurrency)
        snapshot = await make_snapshot(self.cli_args.snapshot, digest, semaphore)

        config = AugmentConfig(
            cosign=CosignClient(
                CosignConfig(verify_key=self.cli_args.verification_key)
            ),
            verify=self.cli_args.verification_key is not None,
            semaphore=semaphore,
            output_dir=self.cli_args.output,
            release_id=self.cli_args.release_id,
        )
        if not all(await augment_sboms(config, snapshot)):
            self.exit_code = 1

    async def save(self) -> None:
        """
        This method is now a no-op since SBOMs are written directly during the
        augmentation process to avoid accumulating SBOMs in memory.
        """


def get_sbom_to_filename_dict(sboms: list[SBOM]) -> dict[SBOM, str]:
    """
    Get a dictionary mapping SBOMs to file names. Uses uuids as suffixes,
    ensuring no two SBOMs are written to the same file.

    Args:
        sboms: list of augmented SBOM objects

    Returns:
        dict[SBOM, str]: a mapping of SBOMs to file names
    """

    sbom_to_filename: dict[SBOM, str] = {}
    for sbom in sboms:
        while (
            filename := get_randomized_sbom_filename(sbom)
        ) in sbom_to_filename.values():
            pass
        sbom_to_filename[sbom] = filename

    return sbom_to_filename


def get_randomized_sbom_filename(sbom: SBOM) -> str:
    """
    Get a filename for an SBOM. Uses a uuid suffix to try and deduplicate SBOM
    file names.

    Args:
        sbom: augmented SBOM object

    Returns:
        str: File name with uuid suffix to save the SBOM to
    """
    suffix = uuid4().hex
    return f"{sbom.reference.replace('/', '-')}-{suffix}"


async def verify_sbom(sbom: SBOM, image: Image, cosign: Cosign) -> None:
    """
    Verify that the sha256 digest of the specified SBOM matches the value of
    SBOM_BLOB_URL in the provenance for the supplied image. Cosign is used to
    fetch the provenance. If it doesn't match, an SBOMVerificationError is
    raised.

    Args:
        sbom (SBOM): the sbom to verify
        image (Image): image to verify the sbom for
        cosign (Cosign): implementation of the Cosign protocol
    """

    prov = await cosign.fetch_latest_provenance(image)
    prov_sbom_digest = prov.get_sbom_digest(image)

    if prov_sbom_digest != sbom.digest:
        raise SBOMVerificationError(
            prov_sbom_digest,
            sbom.digest,
        )


async def load_sbom(image: Image, cosign: Cosign, verify: bool) -> tuple[SBOM, bool]:
    """
    Download and parse the sbom for the image reference and verify that its digest
    matches that in the image provenance.

    Args:
        image (Image): image to load the sbom for
        cosign (Cosign): implementation of the Cosign protocol
        verify (bool): True if the SBOM's digest should be verified via the
            provenance of the image
    Returns:
        SBOM and True if its attestation was validated successfully,
        SBOM and False otherwise
    """
    sbom = await cosign.fetch_sbom(image)
    attestation_valid = True
    if verify:
        try:
            await verify_sbom(sbom, image, cosign)
        except SBOMVerificationError:
            LOGGER.exception(
                "Attestation verification failed for image '%s'."
                "The released images created from this image will"
                "not be attested with a release time SBOM!",
                image.reference,
            )
            attestation_valid = False
    return sbom, attestation_valid


async def write_sbom(sbom: Any, path: Path) -> None:
    """
    Write an SBOM doc dictionary to a file.
    """
    async with aiofiles.open(path, "w") as fp:
        await fp.write(json.dumps(sbom))


def update_sbom_in_situ(
    repository: ReleaseRepository,
    image: Image,
    sbom: SBOM,
    release_id: ReleaseId | None = None,
) -> bool:
    """
    Determine the matching SBOM handler and update the SBOM with release-time
    information in situ.

    Args:
        repository (Component): The repository the image is released to.
        image (Image): Object representing an image being released.
        sbom (dict): SBOM parsed as dictionary.
        release_id: release id to be added to the SBOM's annotations, optional
    """

    if sbom.format in SPDXVersion2.supported_versions:
        SPDXVersion2().update_sbom(repository, image, sbom.doc, release_id)
        return True

    # The CDX handler does not support updating SBOMs for index images, as those
    # are generated only as SPDX in Konflux.
    if sbom.format in CycloneDXVersion1.supported_versions and not isinstance(
        image, IndexImage
    ):
        CycloneDXVersion1().update_sbom(repository, image, sbom.doc, release_id)
        return True

    return False


async def update_sbom(
    config: AugmentConfig,
    repository: ReleaseRepository,
    image: Image,
) -> SBOMRefDetail | None:
    """
    Get an augmented SBOM of an image in a repository.

    Determines format of the SBOM and calls the correct handler.

    Args:
        config: Configuration for SBOM augmentation.
        repository: The repository the image is released to.
        image: Object representing an image or an index image being released.

    Returns:
        Detail of the augmented SBOM if it was successfully enriched,
        None otherwise.
    """

    async with config.semaphore:
        try:
            sbom, attestation_valid = await load_sbom(
                image, config.cosign, config.verify
            )

            if not update_sbom_in_situ(repository, image, sbom, config.release_id):
                raise SBOMError(f"Unsupported SBOM format for image {image}.")
            sbom.reference = repository.public_repo_url + "@" + image.digest
            path = config.output_dir / get_randomized_sbom_filename(sbom)
            await write_sbom(sbom.doc, path)

            LOGGER.info(
                "Successfully enriched SBOM for image %s "
                "(released to %s and pushed to %s)",
                image,
                repository.public_repo_url,
                repository.internal_repo_url,
            )
            return SBOMRefDetail(
                repository.internal_repo_url + "@" + image.digest,
                sbom.format,
                path,
                attestation_valid,
            )
        except Exception:  # pylint: disable=broad-except
            # We catch all exceptions, because we're processing many SBOMs
            # concurrently and an uncaught exception would halt all concurrently
            # running updates.
            LOGGER.exception(
                "Failed to enrich SBOM for image %s (released to %s).",
                image,
                repository.public_repo_url,
            )
            return None


async def update_component_sboms(
    config: AugmentConfig,
    component: Component,
) -> list[SBOMRefDetail | None]:
    """
    Update SBOMs for a component.

    Handles multiarch images as well.

    Args:
        config: Configuration for SBOM augmentation.
        component: Object representing a component being released.

    Returns:
        True if all SBOMs were successfully enriched, False otherwise.
    """
    if isinstance(component.image, IndexImage):
        # If the image of a component is a multiarch image, we update the SBOMs
        # for both the index image and the child single arch images.
        index = component.image
        update_tasks = [
            update_sbom(config, repo, index) for repo in component.release_repositories
        ]
        for child in index.children:
            update_tasks.extend(
                [
                    update_sbom(config, repo, child)
                    for repo in component.release_repositories
                ]
            )

    else:
        # Single arch image
        update_tasks = [
            update_sbom(
                config,
                repo,
                component.image,
            )
            for repo in component.release_repositories
        ]
    results = await asyncio.gather(*update_tasks)
    return results


async def augment_sboms(
    config: AugmentConfig,
    snapshot: Snapshot,
) -> list[SBOMRefDetail | None]:
    """
    Update component SBOMs with release-time information based on a Snapshot.

    Args:
        config: Configuration for SBOM augmentation.
        snapshot: An object representing a snapshot being released.

    Returns:
        True if all SBOMs were successfully enriched, False otherwise.
    """
    results = await asyncio.gather(
        *[
            update_component_sboms(config, component)
            for component in snapshot.components
        ],
    )
    # Flatten the nested results
    return list(itertools.chain(*results))
