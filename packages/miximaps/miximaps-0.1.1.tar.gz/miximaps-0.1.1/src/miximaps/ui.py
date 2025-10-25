from IPython.display import Markdown as md
from IPython.display import display
from decimal import *

import matplotlib as mpl

import folium
from functools import partial
import xyzservices.providers as xyz



def base_map(gdf=None, center=None, zoom=10, provider=xyz.CartoDB.Positron, name=""):
    """
    Create a base map using Folium.

    Parameters:
    - gdf: `GeoDataFrame` to use for the center of the map
    - center: [latitude, longitude] for the center of the map
    - zoom: Initial zoom level of the map, scale is 1-18 (zoomed out --> zoomed in)
    - provider: Map tile provider from `xyzservices` (e.g., xyz.CartoDB.Positron, xyz.CartoDB.DarkMatter, etc.)
    - name: Name of the map (will show up if Layer Control is added)

    Returns:
    - folium.Map object
    """
    # if no center is provided, center it near the middle of the US
    if center == None and gdf is not None:
        minx, miny, maxx, maxy = gdf.total_bounds
        center = [(miny + maxy) / 2, (minx + maxx) / 2]
    elif center == None:
        center = [40.69018448848042, -73.98654521557344]  # MIXI lab, Brooklyn

    attr = "miximaps" if not provider.attribution else provider.attribution
    m = folium.Map(name=name, tiles=provider, attr=attr, location=center, zoom_start=zoom)
    return m


def make_labels(m, df, col, style={}):
    """
    Add the string of `col`
    to the center of each shape in `df`
    onto a folium map.
    
    Parameters:
    -----------
    m : folium.Map
        The map to add the labels to.
    df : GeoDataFrame
        The GeoDataFrame to get the labels and locations from.
    col : str
        The column in `df` to use for the labels.
    style : dict
        A dictionary of CSS styles to apply to the labels.

    Returns:
    --------
    folium.Map
        The map with the labels added.

    Example:
    --------

    m = boroughs_df.explore()
    label_style = {
        "font-size": "12pt",
        "font-weight": "bold",
        "color": "black",
        "background-color": "white",
        "border": "2px solid black",
        "border-radius": "5px",
        "padding": "2px"
    }
    m = make_labels(m, boroughs_df, 'boro_name', style=label_style)
    m
    
    """
    style_str = ";".join([f"{k}:{v}" for k, v in style.items()])

    def label(row):
        point = row.geometry.centroid
        html = f"""<div style="{style_str}">{row[col]}</div>"""
        folium.Marker(
            location=(point.y, point.x),
            icon=folium.DivIcon(html=html)).add_to(m)
    df.apply(label, axis=1)
    return m


def popup(cols, style={"min-width": "200px"}, title=True, fmt_funcs={}):
    """
    Create a function that will generate an HTML popup for a folium map.
    The function will use column names as keys and row data as values.
    If the column name has the special value `----`, a horizontal rule
    will be created as a separator in the popup.

    This is useful to create a popup with a sub-selection of columns
    from a `GeoDataFrame`. Column names are automatically converted
    to "nice names" by replacing underscores with spaces and capitalizing
    the first letter of each word.

    Numerical data is formatted with commas and 3 decimal places.
    For columns with names ending in `_pct`, the data is formatted as a percentage.

    Parameters
    ----------
    cols: list
        The columns to include in the popup
    style: dict
        The CSS style to apply to the popup <div>. Default is {"min-width": "200px"}
    title: bool
        If `True`, the value of the first column will be bold and appear without a label
    fmt_funcs: dict
        A dictionary of functions to apply to the data in each column.
        The keys are the column names and the values are the functions to apply.
    """

    style_str = ";".join([f"{k}:{v}" for k, v in style.items()])

    def html(row):
        def content(c):
            if c == "----":
                return """<hr style="padding: 0;margin:0; margin-bottom: .25em; border: none; border-top: 2px solid black;">"""
            # make a partial of fmt_num that includes the column name

            f = fmt_funcs.get(c, partial(fmt_num, c))
            if c == cols[0] and title:
                return f"<b>{f(row[c])}</b><br>"
            return f"{nice_name(c)}: {f(row[c])}<br>"

        items = [content(c) for c in cols]
        items = "".join(items)
        return f'<div style="{style_str}">{items}</div>'

    return html


def fmt_num(col, n):
    if col.endswith("_pct"):
        return pct(n)
    try:
        n = float(n)
        if round(n) == n:
            return f"{int(n):,}"
        else:
            return f"{n:,.2f}"
    except:
        return n


def hexmap(cmap):

    def f(color):
        return mpl.colors.rgb2hex(cmap(color))

    return f


def pct(n):
    try:
        # n = float(n)
        return f"{n:.1%}"
    except:
        return "-"


def commas(n):
    try:
        float(n)
        return f"{round(n, 3):,}"
    except:
        return "-"


def fmt_table(df, col_map=None, pct_cols=[], num_cols=[]):
    result = df.copy()
    for col in pct_cols:
        result[col] = result[col].apply(pct)

    for col in num_cols:
        result[col] = result[col].apply(commas)

    if col_map:
        result = result.rename(columns=col_map)
    return result


def show_md(s):
    display(md(s))


def infinite():
    n = 0
    while True:
        n += 1
        yield n


def counter():
    x = infinite()
    return x.__next__


def nice_name(n, allcaps=[]):
    if n in allcaps:
        return n.upper()

    return n.replace("_", " ").title()


def round_f(f, places):

    s = str(round(f, places))
    if not "." in s:
        return f

    whole, frac = s.split(".")
    if whole == "0":
        whole = ""
    frac = frac.ljust(places, "0")
    return f"{whole}.{frac}"
