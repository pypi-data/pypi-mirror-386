"""A table widget to select entities."""

import ipywidgets as widgets
import numpy as np
import pandas as pd
import requests
from entitysdk import Client, models, types
from ipydatagrid import DataGrid, TextRenderer
from IPython.display import clear_output, display

from obi_notebook.get_environment import get_environment

LST_MTYPES_ = None
LST_SPECIES_ = None
LST_EMDATASETS_ = None
STR_NO_MTYPE = "NONE"
ENTITY_CLASS_DICT = {"em-cell-mesh": "EMCellMesh"}


def _estimate_column_widths(df, char_width=8, padding=2, max_size=250):
    widths = {}
    for col in df.columns:
        max_len = max(df[col].astype(str).map(len).max(), len(col))
        widths[col] = min(max_size, max_len * char_width + padding)
    return widths


def _resolve_list_to_first_element(obj):
    if isinstance(obj, list):
        if len(obj) > 0:
            return obj[0]["pref_label"]
        return STR_NO_MTYPE
    return obj["pref_label"]


_df_postprocess_funs = {
    "reconstruction-morphology": {"mtypes": _resolve_list_to_first_element},
    "em-cell-mesh": {"dense_reconstruction_cell_id": str},
}


def _list_of_existing_mtypes(entity_core_url, token):
    global LST_MTYPES_
    if LST_MTYPES_ is None:
        response = requests.get(
            f"{entity_core_url}/mtype",
            headers={"authorization": f"Bearer {token}"},
            params={"page_size": 1000},
            timeout=30,
        )
        data = response.json()
        df_mtype = pd.json_normalize(data["data"])
        LST_MTYPES_ = list(df_mtype["pref_label"])
    return LST_MTYPES_


def _list_of_existing_species(entity_core_url, token):
    global LST_SPECIES_
    if LST_SPECIES_ is None:
        response = requests.get(
            f"{entity_core_url}/species",
            headers={"authorization": f"Bearer {token}"},
            params={"page_size": 1000},
            timeout=30,
        )
        data = response.json()
        df_species = pd.json_normalize(data["data"])
        LST_SPECIES_ = list(df_species["name"])
    return LST_SPECIES_


def _list_of_existing_em_dense_datasets(entity_core_url, token):
    global LST_EMDATASETS_
    if LST_EMDATASETS_ is None:
        response = requests.get(
            f"{entity_core_url}/em-dense-reconstruction-dataset",
            headers={"authorization": f"Bearer {token}"},
            params={"page_size": 1000},
            timeout=30,
        )
        data = response.json()
        df_species = pd.json_normalize(data["data"])
        LST_EMDATASETS_ = list(df_species["name"])
    return LST_EMDATASETS_


def get_entities(
    entity_type,
    token,
    result,
    env=None,
    project_context=None,
    return_entities=False,
    multi_select=True,
    page_size=10,
    show_pages=True,
    add_columns=None,
    default_scale=None,
    exclude_scales=None,
):
    """Select entities of type entity_type and add them to result.

    Note: The 'result' parameter is a mutable object (a list) that is modified in-place
      and also returned.
    """
    if env is None:
        env = get_environment()
    if page_size is not None:
        if page_size <= 0:
            raise ValueError("ERROR: Page size must be larger than 0!")
        # TODO: Could add an upper limit as well here

    if add_columns is None:
        add_columns = []
    if exclude_scales is None:
        exclude_scales = []

    subdomain = "www" if env == "production" else "staging"
    entity_core_url = f"https://{subdomain}.openbraininstitute.org/api/entitycore"

    # Widgets
    filters_dict = {}
    if entity_type == "circuit":
        scale_options = [
            _scale.value for _scale in types.CircuitScale if _scale.value not in exclude_scales
        ]
        if default_scale is None or default_scale not in scale_options:
            default_scale = scale_options[0]
        scale_filter = widgets.Dropdown(
            options=scale_options,
            value=default_scale,
            description="Scale:",
        )
        filters_dict["scale"] = scale_filter
        filters_dict["name__ilike"] = widgets.Text(description="Name:")
    elif entity_type == "reconstruction-morphology" or entity_type == "cell-morphology":
        lst_mtypes = _list_of_existing_mtypes(entity_core_url, token) + [""]
        mtype_filter = widgets.Combobox(
            placeholder="Select M-Type",
            description="M-Type:",
            options=lst_mtypes,
            ensure_option=True,
        )
        filters_dict["mtype__pref_label"] = mtype_filter
        lst_species = _list_of_existing_species(entity_core_url, token) + [""]
        species_filter = widgets.Dropdown(options=lst_species, value="", description="Species:")
        filters_dict["species__name"] = species_filter
        filters_dict["name__ilike"] = widgets.Text(description="Name:")
    elif entity_type == "em-cell-mesh":
        lst_em_datasets = _list_of_existing_em_dense_datasets(entity_core_url, token) + [""]
        em_dataset_filter = widgets.Combobox(
            placeholder="Select EM Dataset",
            description="EM-Dataset:",
            options=lst_em_datasets,
            ensure_option=True,
        )
        filters_dict["em_dense_reconstruction_dataset__name__ilike"] = em_dataset_filter
        filters_dict["dense_reconstruction_cell_id"] = widgets.Text(description="Cell ID:")

    if show_pages:
        filters_dict["page"] = widgets.Dropdown(
            options=[1],
            value=1,
            description="Results page:",
            disabled=False,
            style={"description_width": "auto"},
            layout=widgets.Layout(width="max-content"),
        )

    # Output area
    output = widgets.Output()

    # Fetch and display function
    def fetch_data(filter_values):
        if page_size is None:
            params = {}
        else:
            params = {"page_size": page_size}
        for k, v in filter_values.items():
            if isinstance(v, str):
                if len(v.strip()) == 0:
                    continue
            params[k] = v

        headers = {"authorization": f"Bearer {token}"}
        if project_context:
            headers["virtual-lab-id"] = str(project_context.virtual_lab_id)
            headers["project-id"] = str(project_context.project_id)
        response = requests.get(
            f"{entity_core_url}/{entity_type}",
            headers=headers,
            params=params,
            timeout=30,
        )

        try:
            data = response.json()
            df = pd.json_normalize(data["data"])
            pagination = data["pagination"]
            return df, pagination
        except Exception as e:
            print("Error fetching or parsing data:", e)
            return pd.DataFrame(), None

    grid = None

    # On change callback
    def on_change(change=None):
        nonlocal result
        nonlocal grid
        with output:
            clear_output()
            filter_values = {k: v.value for k, v in filters_dict.items()}
            df, pagination = fetch_data(filter_values)

            proper_columns = [
                "id",
                "name",
                "description",
                "brain_region.name",
                "subject.species.name",
                "species.name",  # For morphologies
            ] + add_columns
            if len(df) == 0:
                if show_pages and filters_dict["page"].value != 1:
                    filters_dict["page"].options = [1]  # Will update .value as well
                else:
                    print("no results")
                return

            proper_columns = [_col for _col in proper_columns if _col in df.columns]
            df = df[proper_columns].reset_index(drop=True)

            for colname, fun in _df_postprocess_funs.get(entity_type, {}).items():
                if colname in df.columns:
                    df[colname] = df[colname].apply(fun)

            if show_pages:
                num_pages = np.maximum(
                    1, np.ceil(pagination["total_items"] / pagination["page_size"]).astype(int)
                )
                filters_dict["page"].options = range(1, num_pages + 1)
                df.index = df.index + (pagination["page"] - 1) * pagination["page_size"]

            column_widths = _estimate_column_widths(df)
            grid = DataGrid(
                df,
                layout={"height": "300px"},
                # auto_fit_columns=True,
                auto_fit_params={"area": "all"},
                selection_mode="row",  # Enable row selection
                column_widths=column_widths,
            )
            grid.default_renderer = TextRenderer()
            display(grid)

            def on_selection_change(event, grid=grid):
                with output:
                    if not multi_select and len(grid.selections) > 0:
                        if (event["new"][-1]["r1"] != event["new"][-1]["r2"]) or len(
                            grid.selections
                        ) > 1:  # Multiple rows selected
                            if event["new"][-1]["r1"] == event["old"][-1]["r1"]:  # r1 unchanged
                                new_r = event["new"][-1]["r1"]
                            else:  # r2 unchanged
                                new_r = event["new"][-1]["r2"]
                            # Enforce selection of a single row (last one that was selected)
                            grid.selections = [
                                {
                                    "r1": new_r,
                                    "r2": new_r,
                                    "c1": grid.selections[-1]["c1"],
                                    "c2": grid.selections[-1]["c2"],
                                }
                            ]
                    result.clear()
                    l_ids = set()
                    for selection in grid.selections:
                        for row in range(selection["r1"], selection["r2"] + 1):
                            l_ids.add(df.iloc[row]["id"])

                    if return_entities:
                        client = Client(
                            api_url=entity_core_url,
                            project_context=project_context,
                            token_manager=token,
                        )

                        entity_class_default = "".join(
                            [_token.capitalize() for _token in entity_type.split("-")]
                        )
                        entity_class_name = ENTITY_CLASS_DICT.get(entity_type, entity_class_default)
                        model_class = getattr(models, entity_class_name)
                        retrieved_entities = client.search_entity(
                            entity_type=model_class, query={"id__in": list(l_ids)}
                        )
                        result.extend(retrieved_entities)
                    else:
                        result.extend(l_ids)

            grid.observe(on_selection_change, names="selections")
            grid.selections = [{"r1": 0, "r2": 0, "c1": 0, "c2": len(column_widths)}]

    for filter_ in filters_dict.values():
        filter_.observe(on_change, names="value")

    # Display
    display(widgets.HBox(list(filters_dict.values())), output)

    # Initial load
    on_change()

    return result
