from pyinaturalist.node_api import get_taxa_autocomplete

from naturtag.widgets import AutocompleteSearch


class TaxonAutocompleteSearch(AutocompleteSearch):
    """ Autocomplete search for iNaturalist taxa """

    async def get_autocomplete(self, search_str):
        """ Get taxa autocomplete search results, as display text + other metadata """

        async def _get_taxa_autocomplete():
            return get_taxa_autocomplete(q=search_str).get('results', [])

        def get_dropdown_info(taxon):
            common_name = (
                f' ({taxon["preferred_common_name"]})' if 'preferred_common_name' in taxon else ''
            )
            display_text = f'{taxon["rank"].title()}: {taxon["name"]}{common_name}'
            return {
                'text': display_text,
                'suggestion_text': taxon['matched_term'],
                'metadata': taxon,
            }

        results = await (_get_taxa_autocomplete())
        return [get_dropdown_info(taxon) for taxon in results]
