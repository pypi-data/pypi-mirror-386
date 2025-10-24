from datetime import datetime
import logging

import requests

from dibisoplot.biso import AnrProjects
from dibisoplot.biso import Chapters
from dibisoplot.biso import CollaborationMap
from dibisoplot.biso import CollaborationNames
from dibisoplot.biso import Conferences
from dibisoplot.biso import EuropeanProjects
from dibisoplot.biso import Journals
from dibisoplot.biso import JournalsHal
from dibisoplot.biso import OpenAccessWorks
from dibisoplot.biso import PrivateSectorCollaborations
from dibisoplot.biso import WorksBibtex
from dibisoplot.biso import WorksType

from dibisoreporting import DibisoReporting

from dibisoreporting.utils import escape_for_latex

from dibisoplot._version import __version__ as dibisoplot_version
from dibisoreporting._version import __version__ as dibisoreporting_version


class Biso(DibisoReporting):
    """
    Class to generate the BiSO report

    :cvar class_mapping: Dictionary that maps class names to actual classes
    :cvar default_plot_main_color: Default color for the main plot (#004e7d)
    :cvar default_visualizations: Dictionary contains each type of plot to include in the report with the parameters of
        each plot.
    """

    # Map class names to actual classes
    class_mapping = {
        "AnrProjects": AnrProjects,
        "Chapters": Chapters,
        "CollaborationMap": CollaborationMap,
        "CollaborationNames": CollaborationNames,
        "Conferences": Conferences,
        "EuropeanProjects": EuropeanProjects,
        "Journals": Journals,
        "JournalsHal": JournalsHal,
        "OpenAccessWorks": OpenAccessWorks,
        "PrivateSectorCollaborations": PrivateSectorCollaborations,
        "WorksBibtex": WorksBibtex,
        "WorksType": WorksType
    }

    default_plot_main_color = "#004e7d"

    # an empty list means that the visualization won't be done, an empty dictionary in a list means that the
    # visualization will be done with the default values
    default_visualizations =  {
        "AnrProjects": [
            {
                "max_plotted_entities": 20
            }
        ],
        "Chapters": [{}],
        "CollaborationMap": [
            {
                "name": "world",
                "countries_to_ignore": ["France"],
                "stats_to_save": {
                    "collaborations_nb": "collaborationsnb",
                    "institutions_nb": "institutionsnb",
                    "countries_nb": "countriesnb"
                },
            },
            {
                "name": "europe",
                "resolution": 50,
                "map_zoom": True,
            }
        ],
        "CollaborationNames": [
            {
                "countries_to_exclude": ["fr"],
                "max_plotted_entities": 40
            }
        ],
        "Conferences": [
            {
                "max_plotted_entities": 40
            }
        ],
        "EuropeanProjects": [
            {
                "max_plotted_entities": 20
            }
        ],
        "Journals": [
            {
                "stats_to_save": {
                    "nb_works": "bsojournalsnbworks",
                    "nb_works_found_in_bso": "bsojournalsnbworksfoundinbso",
                    "nb_journals": "bsojournalsnbjournals",
                    "bso_version": "bsojournalsbsoversion"
                },
            }
        ],
        "JournalsHal": [
            {
                "max_plotted_entities": 40
            }
        ],
        "OpenAccessWorks": [
            {
                "stats_to_save": {
                    "oa_works_period": "oaworksperiod"
                }
            }
        ],
        "PrivateSectorCollaborations": [
            {
                "max_plotted_entities": 35
            }
        ],
        "WorksBibtex": [
            {
                "max_plotted_entities": 1000
            }
        ],
        "WorksType": [{}],
    }


    def __init__(
            self,
            entity_id: str,
            year: int | None = None,
            entity_acronym: str = "",
            entity_full_name: str = "",
            latex_main_file_path: str | None = None,
            latex_main_file_url: str | None = None,
            latex_biblio_file_path: str | None = None,
            latex_biblio_file_url: str | None = None,
            latex_template_path: str | None = None,
            latex_template_url: str | None = None,
            max_entities: int | None = 1000,
            max_plotted_entities: int = 25,
            plot_main_color: str | None = None,
            root_path: str | None = None,
            watermark_text: str = "",
            **kwargs
    ):
        """
        Initialize the Biso class with the given parameters.

        :param entity_id: The HAL collection identifier. This usually refers to the entity acronym.
        :type entity_id: str
        :param year: The year for which to fetch data. If None, uses the current year.
        :type year: int | None, optional
        :param entity_acronym: The full acronym of the entity. Default to entity_id.
        :type entity_acronym: str
        :param entity_full_name: The full name of the entity.
        :type entity_full_name: str
        :param latex_main_file_path: Path to a single LaTeX main file. This file is the one to use to compile the
            report. It will copy the main file to root_path. Default to None. If None, doesn't try getting the main file
            from the path. If both latex_main_file_path and latex_main_file_url are not None, the library will first try
            to get the main file from the path.
        :type latex_main_file_path: str | None, optional
        :param latex_main_file_url: URL to download a single LaTeX main file. It will download the file directly
            to root_path. Default to None. If None, doesn't try getting the main file from the URL.
        :type latex_main_file_url: str | None, optional
        :param latex_biblio_file_path: Path to a single LaTeX biblio file. This file is the one to use to compile the
            bibliography. It will copy the biblio file to root_path. Default to None. If None, doesn't try getting the
            biblio file from the path. If both latex_biblio_file_path and latex_biblio_file_url are not None, the
            library will first try to get the biblio file from the path.
        :type latex_biblio_file_path: str | None, optional
        :param latex_biblio_file_url: URL to download a single LaTeX biblio file. It will download the file directly
            to root_path. Default to None. If None, doesn't try getting the biblio file from the URL.
        :type latex_biblio_file_url: str | None, optional
        :param latex_template_path: Path to the LaTeX template files. It will copy the templates files to root_path.
            Default to None. If None, doesn't try getting the template from the path. If both latex_template_path and
            latex_template_url are not None, the library will first try to get the template from the path.
        :type latex_template_path: str | None, optional
        :param latex_template_url: URL to a GitHub repository containing the template. It will get the latest repository
            release and extract it to get the template files. Default to None. If None, doesn't try getting the template
            from the URL.
        :type latex_template_url: str | None, optional
        :param max_entities: Default maximum number of entities used to create the plot. Default 1000.
            Set to None to disable the limit. This value limits the number of queried entities when doing analysis.
            For example, when creating the collaboration map, it limits the number of works to query from HAL to extract the
            collaborating institutions from.
        :type max_entities: int | None, optional
        :param max_plotted_entities: Maximum number of bars in the plot or rows in the table. Default to 25.
        :type max_plotted_entities: int, optional
        :param plot_main_color: Main color used in the plots. Default to "blue". Plotly color.
        :type plot_main_color: str, optional
        :param root_path: Path to the root directory where the report and figures will be generated.
        :type root_path: str
        :param watermark_text: The text to be used as a watermark in the report. Default to "" (no watermark).
        :type watermark_text: str
        """

        super().__init__(
            entity_id,
            year,
            latex_main_file_path=latex_main_file_path,
            latex_main_file_url=latex_main_file_url,
            latex_biblio_file_path=latex_biblio_file_path,
            latex_biblio_file_url=latex_biblio_file_url,
            latex_template_path=latex_template_path,
            latex_template_url=latex_template_url,
            max_entities=max_entities,
            max_plotted_entities=max_plotted_entities,
            plot_main_color=plot_main_color,
            root_path = root_path
        )

        if not entity_acronym:
            entity_acronym = str(entity_id)
        self.entity_acronym = entity_acronym
        self.entity_full_name = entity_full_name
        self.watermark_text = watermark_text

        self.data_fetch_date = datetime.now().strftime("%d/%m/%Y")

        self.kwargs = kwargs


    def generate_report(
            self,
            visualizations_to_make: dict[str, list[dict]] | None = None,
            import_default_visualizations = True
    ):
        """
        Generate the report by calling the specified functions with their parameters to create the desired
        visualizations. To select which visualization to make and configure them, you can use `visualizations_to_make`
        as follows:

        .. code-block:: python

            visualizations_to_make = {
                "AnrProjects": [
                    { "name": "anr1", "param1": "value1", "param2": "value2" },
                    { "name": "anr2", "param1": "value3", "param2": "value4" }
                ],
                "Chapters": [
                    { "name": "chapter1", "param1": "value1", "param2": "value2" }
                ],
                "CollaborationMap": [
                    { "name": "collab1", "max_entities": 1000, "resolution": 50, "map_zoom": True },
                    { "name": "collab2", "max_entities": 500, "resolution": 100, "map_zoom": False }
                ],
                "CollaborationNames": [
                    {}
                ],
                "Conferences": []
            }

        This example, will create:
          * 2 AnrProjects visualizations (with the parameters defined in the dictionaries)
          * 1 Chapters visualization
          * 2 CollaborationMaps visualizations
          * 1 Conferences CollaborationNames (with the default parameters as there is one empty dictionary)
          * 0 Conferences visualizations (as the list is empty)

        :param visualizations_to_make: A dictionary specifying which visualizations to make and their parameters.
        :type visualizations_to_make: list[dict[str, Any]]
        :param import_default_visualizations: Whether to import default visualizations settings. Defaults to True.
            To not generate a plot, set its dictionary in import_default_visualizations to an empty list.
            Example: If you don't want to generate the Conferences visualization, you can set
            import_default_visualizations as follows: ``import_default_visualizations = {"Conferences": []}``.
        :type import_default_visualizations: bool
        """

        # check that the HAL collection ID is valid
        url = f"https://api.archives-ouvertes.fr/search/?q=collCode_s:{self.entity_id}&wt=json&rows=0"
        coll_exists = requests.get(url).json().get('response',{}).get('numFound', 0) > 0
        if not coll_exists:
            logging.warning(f"Collection ID {self.entity_id} does not exist in HAL.")

        self.add_marco("reportyear", escape_for_latex(str(self.year)))
        self.add_marco("halcollectionid", escape_for_latex(self.entity_id))
        self.add_marco("labacronym", escape_for_latex(self.entity_acronym))
        self.add_marco("labfullname", escape_for_latex(self.entity_full_name))
        self.add_marco("datafetchdate", escape_for_latex(self.data_fetch_date))
        self.add_marco("watermarktext", escape_for_latex(self.watermark_text))
        self.macros.append("")
        self.add_marco("dibisoplotversion", escape_for_latex(dibisoplot_version))
        self.add_marco("dibisoreportingversion", escape_for_latex(dibisoreporting_version))
        self.macros.append("")

        super().generate_report(visualizations_to_make, import_default_visualizations)


