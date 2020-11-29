from logging import basicConfig
from re import DOTALL, MULTILINE, compile

import click
from click_help_colors import HelpColorsCommand

from naturtag.image_glob import glob_paths
from naturtag.inat_metadata import strip_url
from naturtag.tagger import tag_images

CODE_BLOCK = compile(r'```\n(.+?)```\s*\n', DOTALL)
CODE_INLINE = compile(r'`([^`]+?)`')
HEADER = compile(r'^#+\s*(.*)$', MULTILINE)


def colorize_help_text(text):
    """ An ugly hack to make help text prettier """
    text = HEADER.sub(click.style(r'\1:', 'blue'), text)
    text = CODE_BLOCK.sub(click.style(r'\1', 'cyan'), text)
    text = CODE_INLINE.sub(click.style(r'\1', 'cyan'), text)
    return text


def _strip_url(ctx, param, value):
    return strip_url(value)


@click.command(cls=HelpColorsCommand, help_headers_color='blue', help_options_color='cyan')
@click.pass_context
@click.option(
    '-c', '--common-names', is_flag=True, help='Include common names for all ranks that have them'
)
@click.option('-d', '--darwin-core', is_flag=True, help='Generate Darwin Core metadata')
@click.option(
    '-h', '--hierarchical', is_flag=True, help='Generate pipe-delimited hierarchical keywords'
)
@click.option('-o', '--observation-id', help='Observation ID or URL', callback=_strip_url)
@click.option('-t', '--taxon-id', help='Taxon ID or URL', callback=_strip_url)
@click.option(
    '-x', '--create-xmp', is_flag=True, help="Create XMP sidecar file if it doesn't already exist"
)
@click.option('-v', '--verbose', is_flag=True, help='Show additional debug output')
@click.argument('image_paths', nargs=-1)
def tag(
    ctx,
    observation_id,
    taxon_id,
    common_names,
    darwin_core,
    hierarchical,
    create_xmp,
    image_paths,
    verbose,
):
    """
    Get taxonomy tags from an iNaturalist observation or taxon, and write them to local image
    metadata.

    \b
    ### Data Sources
    Either a taxon or observation may be specified, either by ID or URL.
    For example, all of the following options will fetch the same taxonomy
    metadata:
    ```
    -t 48978
    -t https://www.inaturalist.org/taxa/48978-Dirona-picta
    -o 45524803
    -o https://www.inaturalist.org/observations/45524803
    ```

    \b
    The difference is that specifying a taxon (`-t`) will fetch only taxonomy
    metadata, while specifying an observation (`-o`) will fetch taxonomy plus
    observation metadata.

    \b
    ### Images
    Multiple paths are supported, as well as glob patterns, for example:
    `0001.jpg IMG*.jpg ~/observations/**.jpg`
    If no images are specified, the generated keywords will be printed.

    \b
    ### Keywords
    Keywords will be generated in the format:
    `taxonomy:{rank}={name}`

    \b
    ### DarwinCore
    If an observation is specified, DwC metadata will also be generated, in the
    form of XMP tags. Among other things, this includes taxonomy tags in the
    format:
    `dwc:{rank}="{name}"`

    \b
    ### Sidecar Files
    By default, XMP tags will be written to a sidecar file if it already exists.
    Use the `-x` option to create a new one if it doesn't exist.

    \b
    ### Hierarchical Keywords
    If specified (`-h`), hierarchical keywords will be generated. These will be
    interpreted as a tree structure by image viewers that support them.

    \b
    For example, the following keywords:
    ```
    Animalia
    Animalia|Arthropoda
    Animalia|Arthropoda|Chelicerata
    Animalia|Arthropoda|Hexapoda
    ```

    \b
    Will translate into the following tree structure:
    ```
    Animalia
        ┗━Arthropoda
            ┣━Chelicerata
            ┗━Hexapoda
    ```
    \b
    """
    if not any([observation_id, taxon_id]):
        click.echo(ctx.get_help())
        ctx.exit()
    if all([observation_id, taxon_id]):
        click.secho('Provide either a taxon or an observation', fg='red')
        ctx.exit()

    if verbose:
        basicConfig(level='DEBUG')

    _, keywords, metadata = tag_images(
        observation_id,
        taxon_id,
        common_names,
        darwin_core,
        hierarchical,
        create_xmp,
        glob_paths(image_paths),
    )

    # If no images were specified, just print keywords
    if not image_paths:
        click.echo('\n'.join(keywords))


# Main CLI entry point
main = tag
tag.help = colorize_help_text(tag.help)
