""" Combined entry point for both CLI and GUI """
from naturtag.inat_metadata import get_keywords, get_observation_dwc_terms
from naturtag.models.meta_metadata import MetaMetadata


def tag_images(
    observation_id, taxon_id, common_names, darwin_core, hierarchical, create_xmp_sidecar, images
):
    """
    Get taxonomy tags from an iNaturalist observation or taxon, and write them to local image
    metadata. See :py:func:`~naturtag.cli.tag` for details.
    """
    keywords = get_keywords(
        observation_id=observation_id,
        taxon_id=taxon_id,
        common=common_names,
        hierarchical=hierarchical,
    )
    # TODO: Simplify this a bit
    # TODO: Also get DwC taxonomy metadata if only a taxon ID is provided
    all_metadata = []
    dwc_metadata = {}
    if observation_id and images and darwin_core:
        dwc_metadata = get_observation_dwc_terms(observation_id)
    for image_path in images:
        all_metadata.append(tag_image(image_path, keywords, dwc_metadata, create_xmp_sidecar))

    return all_metadata, keywords, dwc_metadata


def tag_image(image_path, keywords, dwc_metadata, create_xmp_sidecar):
    metadata = MetaMetadata(image_path)
    metadata.update_keywords(keywords)
    metadata.update(dwc_metadata)
    metadata.write(create_xmp_sidecar=create_xmp_sidecar)
    return metadata
