import functools
import datetime
from typing import List, Optional, Union, Tuple
import os
import shutil
import urllib.request as urlrequest
from urllib.error import URLError
import zipfile
from collections import OrderedDict
from ftplib import FTP
from functools import reduce
from pathlib import Path
from warnings import warn

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.img_tiles as cimgt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.transforms import offset_copy
from tqdm import tqdm

# XDG data dir (fallback to ~/.local/share)
xdg_data_home = Path(
    os.getenv("XDG_DATA_HOME", os.path.join(Path.home(), ".local", "share"))
)
data_dir = xdg_data_home / "opendata_dwd"
data_dir.mkdir(parents=True, exist_ok=True)
ftp_url = "opendata.dwd.de"

DEBUG = False

__version__ = "0.1.0"


def shorten_compound_varnames(func):
    @functools.wraps(func)
    def wrapped(variable: str, *args, **kwds) -> str:
        if variable.startswith("solar"):
            variable = "solar"
        return func(variable, *args, **kwds)

    return wrapped


def get_ftp_root(*, era: str = "historical", time: str = "hourly") -> str:
    template_root = "climate_environment/CDC/observations_germany/climate"
    template = f"{template_root}/{time}/{{variable}}"
    if era:
        return f"{template}/{era}"
    return template


@shorten_compound_varnames
def get_ftp_variable_root(
    variable: str, *, era: str = "historical", time: str = "hourly"
) -> str:
    template = get_ftp_root(era=era, time=time)
    return template.format(variable=variable)


@shorten_compound_varnames
def get_ftp_path(
    variable: str, *, time: str = "hourly", era: str = "historical"
) -> str:
    ftp_root = get_ftp_root(era=era, time=time)
    return ftp_root.format(variable=found_in[time][variable], era=era)


def get_zip_filename(variable: str, time: str = "hourly", **metadata) -> str:
    match time:
        case "10_minutes":
            variable_short = variable_shorts[time][variable]
            time_str = f"10minutenwerte_{variable_short}"
        case "hourly":
            variable_short = variable_shorts[time][variable]
            time_str = f"stundenwerte_{variable_short}"
        case "daily":
            variable_short = variable_shorts[time][variable]
            time_str = f"tageswerte_{variable_short}"
        case _:
            raise NotImplementedError(
                f"Discretization {time=} not implemented."
            )
    return f"{time_str}_{metadata['Stations_id']:05d}"


def get_data_url(variable: Optional[str] = None, **kwds) -> str:
    ftp_root = get_ftp_root(**kwds)
    template = f"ftp://{ftp_url}/{ftp_root}"
    if variable is None:
        return template
    return template.format(variable=variable)


@shorten_compound_varnames
def get_url(variable, zip_filename, *, time="hourly", era="historical"):
    data_url = get_data_url(era=era, time=time)
    return os.path.join(
        data_url.format(variable=found_in[time][variable]), zip_filename
    )


@shorten_compound_varnames
def get_zip_path(variable: str) -> Path:
    return data_dir / variable


def get_meta_filename(variable_short: str, time: str = "hourly") -> str:
    match time:
        case "10_minutes":
            variable_short_lower: str = variable_short.lower()
            return (
                f"zehn_min_{variable_short_lower}_Beschreibung_Stationen.txt"
            )
        case "hourly":
            return f"{variable_short}_Stundenwerte_Beschreibung_Stationen.txt"
        case "daily":
            return f"{variable_short}_Tageswerte_Beschreibung_Stationen.txt"
        case _:
            raise RuntimeError(
                "time parameter not understood.\n"
                f"Must be one of ('10_minutes', 'hourly', 'daily'), not {time}"
            )


def get_description_name(variable_short: str, time: str = "hourly") -> str:
    match time:
        case "10_minutes":
            time_str = "10min"
        case _:
            time_str = time
    var_str = variable_short.lower()
    return f"DESCRIPTION_obsgermany-climate-{time_str}-{var_str}_en.pdf"


def get_meta_url(
    variable: str, era: Optional[str] = None, time: str = "hourly"
) -> str:
    data_url = get_data_url(era=era, time=time).format(
        variable=found_in[time][variable]
    )
    variable_short = variable_shorts[time][variable]
    meta_filename = get_meta_filename(variable_short, time)
    return f"{data_url}/{meta_filename}"


def get_description_url(
    variable: str, era: Optional[str] = None, time: str = "hourly"
) -> str:
    data_url = get_data_url(era=era, time=time).format(
        variable=found_in[time][variable]
    )
    variable_short = variable_shorts[time][variable]
    pdf_filename = get_description_name(variable_short, time)
    return f"{data_url}/{pdf_filename}"


date_formats = {
    "10_minutes": "%Y%m%d%H%M",
    "hourly": "%Y%m%d%H",
    "hourly_solar": "%Y%m%d%H:%M",
    "daily": "%Y%m%d",
}
variable_shorts_hourly = {
    "cloudiness": "N",
    # "solar": "SD",
    "solar": "ST",
    "solar_diffuse": "DS",
    # "solar_global": "GS",
    "solar_global": "ST",
    "solar_duration": "SD",
    "solar_long": "LS",
    "sun": "SD",
    "precipitation": "RR",
    "pressure": "P0",
    "air_temperature": "TU",
    "soil_temperature": "EB",
    "relative_humidity": "TU",  # is found in air temperature files
    "wind": "FF",
    "wind_speed": "F",
    "wind_direction": "D",
    "daily": "KL",
}
variable_shorts_daily = {
    "precipitation_daily": "KL",
    "air_temperature": "KL",
    "air_temperature_max": "KL",
    "air_temperature_min": "KL",
    "solar_in": "ST",
    "solar": "solar",
    "solar_global": "solar",
    "wind": "FF",
    "sun": "SD",
}
variable_shorts_10_minutes = {
    key: "SOLAR" if key.startswith("solar") else val
    for key, val in variable_shorts_daily.items()
}
variable_shorts_10_minutes["solar"] = "SD"
variable_shorts = {
    "hourly": variable_shorts_hourly,
    "daily": variable_shorts_daily,
    "10_minutes": variable_shorts_10_minutes,
}
found_in_10_minutes = {key: key for key in variable_shorts_10_minutes.keys()}
# found_in_10_minutes["solar_global"] = "solar"
found_in_hourly = {key: key for key in variable_shorts_hourly.keys()}
found_in_hourly["relative_humidity"] = "air_temperature"
found_in_daily = {key: key for key in variable_shorts_daily.keys()}
found_in_daily.update(
    {
        "relative_humidity": "air_temperature",
        "air_temperature_max": "kl",
        "air_temperature_min": "kl",
        "precipitation_daily": "kl",
        "solar": "solar",
    }
)
found_in = {
    "daily": found_in_daily,
    "hourly": found_in_hourly,
    "10_minutes": found_in_10_minutes,
}
variable_cols = {
    "wind_speed": ["F"],
    "wind_direction": ["D"],
    "wind": ["F", "D"],
    "air_temperature": ["TT_TU"],
    "air_temperature_max": ["TXK"],
    "air_temperature_min": ["TNK"],
    "precipitation_daily": ["RSK"],
    "relative_humidity": ["RF_TU"],
    # TODO: 10 refers to 10 minute interval
    "solar_diffuse": ["DS_10"],
    "solar_global_10_minutes": ["GS_10"],
    "solar_global_hourly": ["FG_LBERG"],
    "solar_duration": ["SD_10"],
    "solar_long": ["LS_10"],
    "solar_in": ["FG_STRAHL"],
    "sun": ["SD_SO"],
    "precipitation": ["R1"],
    "pressure": ["P0"],
}
cols_variable = {val[0]: key for key, val in variable_cols.items()}
cols_variable["F"] = "wind_speed"
variable_omits_era = {key: False for key in variable_shorts_hourly.keys()}
variable_omits_era.update(
    {
        # "solar": True,
        "solar_in": True,
    }
)
header_dtypes = OrderedDict(
    (
        ("Stations_id", int),
        ("von_datum", int),
        ("bis_datum", int),
        ("Stationshoehe", float),
        ("geoBreite", float),
        ("geoLaenge", float),
        ("Stationsname", str),
        ("Bundesland", str),
    )
)
meta_header = list(header_dtypes.keys())
data_dir.mkdir(parents=True, exist_ok=True)


def do_download_pdf(
    variable: str, era: Optional[str] = None, time: str = "hourly"
) -> None:
    # as the pdf filenames are not named consistently (variable
    # naming, varying "-" and "_" as seperators), just look for the
    # english pdf in the variable's folder and download it
    trunc_names = ("wind", "solar")
    for trunc_name in trunc_names:
        if variable.startswith(trunc_name):
            variable = trunc_name
            break
    pdf_filename = get_description_name(variable, time=time)
    pdf_filepath = data_dir / pdf_filename
    if not pdf_filepath.exists():
        ftp = FTP(ftp_url)
        ftp.login()
        ftp_path = get_ftp_variable_root(variable, era=None, time=time)
        if DEBUG:
            print(ftp_path)
        remote_pdf_filepath = [
            filepath
            for filepath in ftp.nlst(ftp_path)
            if filepath.endswith("en.pdf")
        ]
        if len(remote_pdf_filepath) == 0:
            raise URLError(f"Could not find pdf in ftp://{ftp_url}/{ftp_path}")
        url = f"ftp://{ftp_url}/{remote_pdf_filepath[0]}"
        try:
            with urlrequest.urlopen(url) as req:
                content = req.read()
        except URLError:
            raise URLError(f"Could not download:\n{url}")
        else:
            with pdf_filepath.open("wb") as fi:
                fi.write(content)
        ftp.close()


def load_metadata(
    variable: str,
    era: Optional[str] = None,
    time: str = "hourly",
    redownload: bool = False,
) -> pd.DataFrame:
    trunc_names = ("wind", "solar")
    for trunc_name in trunc_names:
        if variable.startswith(trunc_name):
            variable = trunc_name
            break
    meta_filename = f"metadata_{variable}_{time}.txt"
    meta_filepath = data_dir / meta_filename
    if redownload or not meta_filepath.exists():
        era = None if variable_omits_era[variable] else era
        url = get_meta_url(variable, era=era, time=time)
        try:
            with urlrequest.urlopen(url) as req:
                content = req.read()
        except URLError:
            raise URLError(f"Could not download:\n{url}")
        else:
            with meta_filepath.open("w") as fi:
                fi.write(content.decode("latin-1"))

    # def date_parser(stamp):
    #     return datetime.strptime(stamp, "%Y%m%d")

    # ok, this is brittle as the DWD might not be consistent about
    # column widths, but colspecs=infer only checks the first 100
    # lines and ends up with widths that are too small for some
    # station names.
    colspecs = [
        (0, 5),
        (6, 14),
        (15, 23),
        (23, 38),
        (38, 50),
        (50, 60),
        (61, 102),
        (102, 200),
    ]
    df = pd.read_fwf(
        meta_filepath,
        skiprows=[0, 1],
        colspecs=colspecs,
        dtype=header_dtypes,
        parse_dates=[1, 2],
        # date_parser=date_parser,
        date_format="%Y%m%d",
    )
    df.columns = meta_header
    return df


def _load_station_one_var(
    station_name: str,
    variable: str,
    *,
    era: Optional[str] = None,
    time: str = "hourly",
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    redownload: bool = False,
    download_pdf: bool = True,
) -> pd.DataFrame:
    if variable.startswith("wind"):
        variable = "wind"
    if variable == "solar_global":
        variable_col = variable_cols[f"{variable}_{time}"]
    else:
        variable_col = variable_cols[variable]
    if variable == "relative_humidity":
        variable = "air_temperature"
    if download_pdf:
        do_download_pdf(variable, era=era, time=time)
    metadata_df = load_metadata(
        variable, era=era, time=time, redownload=redownload
    )
    metadata_df = metadata_df[metadata_df["Stationsname"] == station_name]
    if DEBUG:
        print(metadata_df)
    if metadata_df.size == 0:
        print(f"No {variable} for {station_name}")
        return pd.DataFrame([])
    metadata = {
        key: val[0] for key, val in metadata_df.to_dict("list").items()
    }
    zip_filename = get_zip_filename(variable, time, **metadata)
    if DEBUG:
        print(zip_filename)
    zip_path = get_zip_path(variable)
    zip_path.mkdir(parents=True, exist_ok=True)
    zip_filepath = zip_path / zip_filename
    if redownload:
        zip_filepaths_existing: List[Path] = []
    else:
        zip_filepaths_existing = list(
            zip_filepath.parent.glob(f"{zip_filepath.name}*.zip")
        )

    if not zip_filepaths_existing:
        print(f"Downloading {zip_filepath.name}*")
        # we do not know what the filename is exactly because at least
        # the "bis_datum" is different in metadata and filename
        ftp = FTP(ftp_url)
        era = None if variable_omits_era[variable] else era
        ftp_path = get_ftp_path(variable, era=era, time=time)
        if DEBUG:
            print(ftp_path)
        ftp.login()
        zip_filenames = [
            name
            for filepath in ftp.nlst(ftp_path)
            if (name := filepath.split("/")[-1]).startswith(zip_filename)
        ]
        if not zip_filenames:
            raise URLError(
                f"Could not find any zip files here ftp://{ftp_url}/{ftp_path}"
            )

        for zip_filename in zip_filenames:
            zip_filepath_zip = zip_filepath.parent / zip_filename
            if zip_filepath_zip in zip_filepaths_existing:
                continue
            zip_filepaths_existing += [zip_filepath_zip]
            url = get_url(variable, zip_filename, time=time, era=era)
            if DEBUG:
                print(url)
            try:
                with zip_filepath_zip.open("wb") as fi:
                    with urlrequest.urlopen(url) as req:
                        content = req.read()
                        fi.write(content)
            except URLError:
                raise URLError(f"Could not download {url}")
        ftp.close()

    filepaths_txt: List[Path] = []
    for zip_filepath_existing in zip_filepaths_existing:
        try:
            with zipfile.ZipFile(str(zip_filepath_existing)) as zif:
                data_name = [
                    name
                    for name in zif.namelist()
                    if name.startswith("produkt_")
                ][0]
                filepath_txt = zip_filepath_existing.with_suffix(".txt")
                filepaths_txt += [filepath_txt]
                if redownload or not filepath_txt.exists():
                    zif.extract(data_name, path=zip_filepath.parent)
                    produkt_path = zip_filepath.parent / data_name
                    shutil.move(produkt_path, filepath_txt)
        except zipfile.BadZipFile:
            warn(
                f"Bad zip file: {zip_filepath_existing}. \n"
                f"I'm deleting the file and recurse."
            )
            zip_filepath_existing.unlink()
            return _load_station_one_var(
                station_name,
                variable,
                era=era,
                time=time,
                redownload=False,
            )
    dfs = []
    for filepath_txt in sorted(filepaths_txt):
        cols = ["MESS_DATUM"] + variable_col
        df = pd.read_csv(
            filepath_txt,
            # sep=r";\s*",
            sep=";",
            skipinitialspace=True,
            index_col=0,
            parse_dates=True,
            date_format=date_formats[time],
            # engine="python",
            usecols=cols,
            na_values="-999",
        )
        # strange, this should have been caught by na_values above
        df = df.where(df != -999, np.nan)
        df.index.name = "time"
        df.columns = [cols_variable[col] for col in cols[1:]]
        df.name = station_name
        if len(dfs):
            if dfs[-1].index[-1] > df.index[0]:
                # make sure we have no overlap
                df = df.loc[dfs[-1].index[-1] :][1:]
        if len(df):
            dfs += [df]

    df = pd.concat(dfs)
    # TODO would be nice if we check this before downloading and opening
    if start_year or end_year:
        start_year = None if start_year is None else str(start_year)
        end_year = None if end_year is None else str(end_year)
        df = df.loc[start_year:end_year]
    # there are duplicates sometimes
    if (duplicate_mask := df.index.duplicated()).any():
        df = df[~duplicate_mask]
    df.name = station_name
    return df


def load_station(
    station_name: str,
    variables: Union[str, List[str]],
    redownload: bool = False,
    era: Optional[str] = None,
    time: str = "hourly",
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> xr.DataArray:
    """
    Load meteorological data for a single station from the DWD open data platform.

    Parameters
    ----------
    station_name : str
        Name of the weather station (e.g., "Berlin", "Munich")
    variables : Union[str, List[str]]
        Variable(s) to load. Can be a string or list of strings.
    redownload : bool, optional
        Force redownload of data files. Default: False
    era : str, optional
        Era of data (e.g., "historical", "recent"). Default: None
    time : str, optional
        Time resolution of data: "hourly", "daily", or "10_minutes". Default: "hourly"
    start_year : int, optional
        Start year for data range. None (default) means from earliest available data.
    end_year : int, optional
        End year for data range. None (default) means to latest available data.

    Returns
    -------
    xr.DataArray
        Data for the requested station and variables
    """
    if isinstance(variables, str):
        variables = (variables,)
    var_list = [
        _load_station_one_var(
            station_name,
            variable,
            redownload=redownload,
            era=era,
            time=time,
            start_year=start_year,
            end_year=end_year,
        )
        for variable in variables
    ]
    var_list = [xr.DataArray(vals) for vals in var_list if vals.size > 0]
    if not var_list:
        warn(f"No data for {station_name} ({variables})")
        return
    da = (
        xr.merge(var_list)
        .rename(dim_1="met_variable")
        .to_array(dim="station", name=station_name)
    )
    return da


def load_data(
    station_names: Union[str, List[str]],
    variables: Union[str, List[str]],
    redownload: bool = False,
    time: str = "hourly",
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    verbose: bool = False,
) -> xr.Dataset:
    """
    Load meteorological data for multiple stations from the DWD open data platform.

    Parameters
    ----------
    station_names : Union[str, List[str]]
        Station name(s) to load. Can be a string or list of strings (e.g., ("Berlin", "Munich"))
    variables : Union[str, List[str]]
        Variable(s) to load. Can be a string or list of strings.
    redownload : bool, optional
        Force redownload of data files. Default: False
    time : str, optional
        Time resolution: "hourly", "daily", or "10_minutes". Default: "hourly"
    start_year : int, optional
        Start year for data range. None (default) means from earliest available data.
    end_year : int, optional
        End year for data range. None (default) means to latest available data.
    verbose : bool, optional
        Show progress bar. Default: False

    Returns
    -------
    xr.Dataset
        Combined data for all requested stations and variables
    """
    progress = tqdm if verbose else lambda x: x
    if isinstance(station_names, str):
        station_names = (station_names,)
    if isinstance(variables, str):
        variables = (variables,)
    data_dict = {
        station_name: station_data
        for station_name in progress(station_names)
        if (
            station_data := load_station(
                station_name,
                variables,
                redownload=redownload,
                time=time,
                start_year=start_year,
                end_year=end_year,
            )
        )
        is not None
    }
    return xr.concat(data_dict.values(), dim="station")


def filter_metadata(
    metadata: pd.DataFrame,
    lon_min: Optional[float] = None,
    lat_min: Optional[float] = None,
    lon_max: Optional[float] = None,
    lat_max: Optional[float] = None,
    start: Optional[datetime.datetime] = None,
    end: Optional[datetime.datetime] = None,
) -> pd.DataFrame:
    lons = metadata["geoLaenge"]
    lats = metadata["geoBreite"]
    starts = metadata["von_datum"]
    ends = metadata["bis_datum"]
    if lon_min is None:
        lon_min = lons.min()
    if lat_min is None:
        lat_min = lats.min()
    if lon_max is None:
        lon_max = lons.max()
    if lat_max is None:
        lat_max = lats.max()
    if start is None:
        start = starts.min()
    if end is None:
        end = ends.max()
    mask = (
        (lons >= lon_min)
        & (lons < lon_max)
        & (lats >= lat_min)
        & (lats < lat_max)
        & (starts < start)
        & (ends > end)
    )
    if not mask.sum():
        warn("No stations match requirements.")
    return metadata[mask]


def get_metadata(
    variables: Union[str, List[str]],
    era: Optional[str] = None,
    time: str = "hourly",
    redownload: bool = False,
) -> pd.DataFrame:
    """
    Get metadata for stations offering requested variables.

    Returns stations that provide all requested variables with their location
    and availability information.

    Parameters
    ----------
    variables : Union[str, List[str]]
        Variable(s) to search for
    era : str, optional
        Era of data (e.g., "historical", "recent"). Default: None
    time : str, optional
        Time resolution: "hourly", "daily", or "10_minutes". Default: "hourly"
    redownload : bool, optional
        Force redownload of metadata. Default: False

    Returns
    -------
    pd.DataFrame
        Metadata for matching stations including name, location, and date range
    """
    if isinstance(variables, str):
        variables = [variables]
    variable_metadata = {
        variable: load_metadata(
            variable, era=era, time=time, redownload=redownload
        )
        for variable in variables
    }
    # find the stations that offer all variables
    station_ids = [var["Stations_id"] for var in variable_metadata.values()]
    station_ids = reduce(np.intersect1d, station_ids)
    metadata = (
        variable_metadata[variables[0]]
        .set_index("Stations_id")
        .loc[station_ids]
    )
    return metadata


def map_stations(
    variables: Union[str, List[str]],
    lon_min: Optional[float] = None,
    lat_min: Optional[float] = None,
    lon_max: Optional[float] = None,
    lat_max: Optional[float] = None,
    start: Optional[datetime.datetime] = None,
    end: Optional[datetime.datetime] = None,
    **skwds,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a map showing which stations provide requested variables in a geographic region.

    Parameters
    ----------
    variables : Union[str, List[str]]
        Variable(s) to search for
    lon_min : float, optional
        Minimum longitude of bounding box. Default: None (world extent)
    lat_min : float, optional
        Minimum latitude of bounding box. Default: None (world extent)
    lon_max : float, optional
        Maximum longitude of bounding box. Default: None (world extent)
    lat_max : float, optional
        Maximum latitude of bounding box. Default: None (world extent)
    start : datetime, optional
        Start date for data availability filter. Default: None (no filtering)
    end : datetime, optional
        End date for data availability filter. Default: None (no filtering)

    Returns
    -------
    tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]
        Figure and axes objects for further customization
    """
    metadata = get_metadata(variables)
    metadata = filter_metadata(
        metadata, lon_min, lat_min, lon_max, lat_max, start, end
    )
    osm_terrain = cimgt.OSM()
    crs = ccrs.PlateCarree()
    land_10m = cfeature.NaturalEarthFeature(
        "cultural",
        "admin_0_countries",
        "10m",
        edgecolor=(0, 0, 0, 0),
        facecolor=(0, 0, 0, 0),
    )
    fig = plt.figure(layout="constrained", **skwds)
    ax = fig.add_subplot(111, projection=osm_terrain.crs)
    geodetic_transform = ccrs.Geodetic()._as_mpl_transform(ax)
    text_transform = offset_copy(geodetic_transform, units="dots", x=-25, y=8)
    lons = metadata["geoLaenge"]
    lats = metadata["geoBreite"]
    station_names = metadata["Stationsname"]
    starts = metadata["von_datum"]  # don't trust this too much!
    ends = metadata["bis_datum"]
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=crs)
    for i in metadata.index:
        text = f"{station_names[i]}\n{starts[i].year}-{ends[i].year}"
        ax.text(lons[i], lats[i], text, fontsize=8, transform=text_transform)
    ax.scatter(lons, lats, transform=crs)
    ax.add_feature(land_10m, alpha=0.1)
    ax.add_image(osm_terrain, 10)
    return fig, ax


def map_stations_var(
    variables: Union[str, List[str]],
    lon_min: Optional[float] = None,
    lat_min: Optional[float] = None,
    lon_max: Optional[float] = None,
    lat_max: Optional[float] = None,
    **skwds,
) -> plt.Figure:
    if isinstance(variables, str):
        variables = [variables]
    n_variables = len(variables)
    variable_metadata = {
        variable: load_metadata(variable) for variable in variables
    }
    all_station_names = [
        variable_metadata[variable]["Stationsname"].values
        for variable in variables
    ]
    station_names_inter = reduce(np.intersect1d, all_station_names)

    osm_terrain = cimgt.OSM()
    crs = ccrs.PlateCarree()
    land_10m = cfeature.NaturalEarthFeature(
        "cultural",
        "admin_0_countries",
        "10m",
        edgecolor=(0, 0, 0, 0),
        facecolor=(0, 0, 0, 0),
    )

    if n_variables == 1:
        fig, axs = plt.subplots()
        axs = [axs]
        ncols = 1
        nrows = 1
    else:
        ncols = 2
        nrows = n_variables // ncols + n_variables % ncols
        fig = plt.figure(**skwds)
    for ax_i, variable in enumerate(variables):
        ax = fig.add_subplot(
            nrows, ncols, ax_i + 1, projection=osm_terrain.crs
        )
        geodetic_transform = ccrs.Geodetic()._as_mpl_transform(ax)
        text_transform = offset_copy(geodetic_transform, units="dots", x=-25)
        station_metadata = variable_metadata[variable]
        lons = station_metadata["geoLaenge"]
        lats = station_metadata["geoBreite"]
        station_names = station_metadata["Stationsname"]
        starts = station_metadata["von_datum"]
        ends = station_metadata["bis_datum"]
        if lon_min is None:
            lon_min = lons.min()
        if lat_min is None:
            lat_min = lats.min()
        if lon_max is None:
            lon_max = lons.max()
        if lat_max is None:
            lat_max = lats.max()
        mask = (
            (lons >= lon_min)
            & (lons < lon_max)
            & (lats >= lat_min)
            & (lats < lat_max)
        )
        lons = lons[mask]
        lats = lats[mask]
        station_names = station_names[mask]
        starts = starts[mask]
        ends = ends[mask]
        ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=crs)
        for i in station_metadata[mask].index:
            text = f"{station_names[i]}\n{starts[i].year}-{ends[i].year}"
            ax.text(
                lons[i], lats[i], text, fontsize=6, transform=text_transform
            )
        ax.scatter(lons, lats, transform=crs)
        red_station_names = np.intersect1d(
            station_names.values, station_names_inter
        )
        ii = np.where(station_names.values == red_station_names[:, None])[1]
        ax.scatter(lons.iloc[ii], lats.iloc[ii], facecolor="red")
        ax.set_title(variable)
        ax.add_feature(land_10m, alpha=0.1)
        ax.add_image(osm_terrain, 10)
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    metadata = get_metadata("solar", time="10_minutes")
    print(metadata)
    solar = _load_station_one_var(
        "Konstanz", "solar_global", time="10_minutes", redownload=False
    )

    from datetime import datetime

    start = datetime(1980, 1, 1)
    end = datetime(2016, 12, 31)
    variables = ("wind", "air_temperature", "sun", "precipitation")
    fig, ax = map_stations(
        variables,
        lon_min=7,
        lat_min=47.4,
        lon_max=12.0,
        lat_max=49.0,
        start=start,
        end=end,
    )
    fig.savefig("../../source/station_map.png")

    data = load_data(
        ("Konstanz", "Feldberg/Schwarzwald"),
        variables=variables,
        start_year=start,
        end_year=end,
    )
    print(data)

    # df = map_stations_var(
    #     ["wind", "air_temperature", "sun", "precipitation"],
    #     lon_min=7,
    #     lat_min=47.4,
    #     lon_max=12.0,
    #     lat_max=49.0,
    # )

    plt.show()
