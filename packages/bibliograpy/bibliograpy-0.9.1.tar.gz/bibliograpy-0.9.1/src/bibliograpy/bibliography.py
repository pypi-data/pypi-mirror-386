from bibliograpy.api_bibtex import *

_SCOPE = {}


ECMA = Misc.generic(cite_key='ecma',
                    organization='ecma international',
                    non_standard=NonStandard(url='https://ecma-international.org'),
                    scope=_SCOPE)

JSON = Misc.generic(cite_key='json',
                    crossref=ECMA,
                    note='ECMA-404',
                    title='The JSON data interchange syntax',
                    non_standard=NonStandard(url='https://ecma-international.org/publications-and-standards/standards/ecma-404/'),
                    scope=_SCOPE)

YAML = Misc.generic(cite_key='yaml',
                    title='YAML™ Specification Index',
                    non_standard=NonStandard(url='https://yaml.org/spec/'),
                    scope=_SCOPE)

BIBLIOGRAPI = Misc.generic(cite_key='bibliograpi',
                           author='Samuel Andrés',
                           title='BibliogrAPI Specification',
                           year='2024',
                           non_standard=NonStandard(url='https://cosmoloj.com/bibapi/'),
                           scope=_SCOPE)

BIBTEX_COM = Misc.generic(cite_key='bibtex_com',
                          title='www.bibtex.com',
                          non_standard=NonStandard(url='https://www.bibtex.com/'),
                          scope=_SCOPE)

BIBTEX_PACKAGE = Misc.generic(cite_key='bibtex_package',
                              title='CTAN Bibtex package documentation',
                              non_standard=NonStandard(url='https://distrib-coffee.ipsl.jussieu.fr/pub/mirrors/ctan/biblio/bibtex/base/btxdoc.pdf'),
                              scope=_SCOPE)

RIS_2001 = Misc.generic(cite_key='ris_2001',
                        month='february',
                        title='RIS Format Specifications',
                        year='2001',
                        non_standard=NonStandard(url='https://web.archive.org/web/20110925024348/http://www.refman.com/support/risformat_intro.asp'),
                        scope=_SCOPE)

RIS_2011 = Misc.generic(cite_key='ris_2011',
                        month='october',
                        title='RIS Format Specifications',
                        year='2011',
                        non_standard=NonStandard(url='https://web.archive.org/web/20120616231500/http://www.refman.com/support/risformat_intro.asp'),
                        scope=_SCOPE)

REFER_MAN = Misc.generic(cite_key='refer_man',
                         title='refer(1) — Linux manual page',
                         non_standard=NonStandard(url='https://man7.org/linux/man-pages/man1/refer.1.html'),
                         scope=_SCOPE)

PUBMED_FORMAT = Misc.generic(cite_key='pubmed_format',
                             title='PubMed format',
                             non_standard=NonStandard(url='https://pubmed.ncbi.nlm.nih.gov/help/#pubmed-format'),
                             scope=_SCOPE)

PUBMED_PUBLICATION_TYPES = Misc.generic(cite_key='pubmed_publication_types',
                                        title='PubMed publication types',
                                        non_standard=NonStandard(url='https://pubmed.ncbi.nlm.nih.gov/help/#publication-types'),
                                        scope=_SCOPE)

MESH_PUBLICATION_TYPES = Misc.generic(cite_key='mesh_publication_types',
                                      title='MESH publication types',
                                      non_standard=NonStandard(url='https://www.nlm.nih.gov/mesh/pubtypes.html'),
                                      scope=_SCOPE)

PUBMED_MEDLINE_PMC_DIFFERENCE = Misc.generic(cite_key='pubmed_medline_pmc_difference',
                                             title='MEDLINE, PubMed, and PMC (PubMed Central): How are they different?',
                                             non_standard=NonStandard(url='https://www.nlm.nih.gov/bsd/difference.html'),
                                             scope=_SCOPE)
