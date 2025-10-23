import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.table import QTable, Table
from astropy.time import Time

from stellarphot import PhotometryData, SourceListData

__all__ = ["add_in_quadrature", "calc_aij_relative_flux", "add_relative_flux_column"]


def add_in_quadrature(array):
    """
    Add an array of numbers in quadrature.
    """
    return np.sqrt((array**2).sum())


def calc_aij_relative_flux(
    star_data,
    comp_stars,
    in_place=True,
    coord_column=None,
    star_id_column="star_id",
    counts_column_name="aperture_net_cnts",
):
    """
    Calculate AstroImageJ-style flux ratios.

    Parameters
    ----------

    star_data : 'stellarphot.PhotometryData'
        Photometry data from one or more images.

    comp_stars : '~astropy.table.Table'
        Table of comparison stars in the field. Must contain a column
        called ``ra`` and a column called ``dec``.
        NOTE that not all
        of the comparison stars will necessarily be used. Stars in
        this table are excluded from the comparison set if, in any
        of the `star_data` for that comparison, the net counts are
        ``NaN`` or if the angular distance between the position in
        the `star_data` and the position in the `comp_stars` table
        is too large.

    in_place : bool,  optional
        If ``True``, add new columns to input table. Otherwise, return
        new table with those columns added.

    coord_column : str,  optional
        If provided, use this column to match comparison stars to coordinates.
        If not provided, the coordinates are generated with SkyCoord.

    counts_column_name : str,  optional
        If provided, use this column to find counts.

    star_id_column : str,  optional
        Name of the column that provides a unique identifier for each
        comparison star.

    Returns
    -------

    `stellarphot.PhotometryData` or None
        The return type depends on the value of ``in_place``. If it is
        ``False``, then the new columns are returned as a separate table,
        otherwise the columns are simply added to the input table.
    """

    # Match comparison star list to instrumental magnitude information
    if star_data["ra"].unit is None:
        unit = "degree"
    else:
        # Pulled this from the source code -- None is ok but need
        # to match the number of coordinates.
        unit = [None, None]

    star_data_coords = SkyCoord(ra=star_data["ra"], dec=star_data["dec"], unit=unit)

    if coord_column is not None:
        comp_coords = comp_stars[coord_column]
    else:
        if comp_stars["ra"].unit is None:
            unit = "degree"
        else:
            # Pulled this from the source code -- None is ok but need
            # to match the number of coordinates.
            unit = [None, None]
        comp_coords = SkyCoord(ra=comp_stars["ra"], dec=comp_stars["dec"], unit=unit)

    # Check for matches of stars in star data to the stars in comp_stars
    # and eliminate as comps any stars for which the separation is bigger
    # than 1.2 arcsec in any of the frames.
    index, d2d, _ = star_data_coords.match_to_catalog_sky(comp_coords)

    # Not sure this is really close enough for a good match...
    good = d2d < 1.2 * u.arcsec

    check_for_bad = Table(
        data=[star_data[star_id_column].data, good], names=["star_id", "good"]
    )
    check_for_bad = check_for_bad.group_by("star_id")
    is_all_good = check_for_bad.groups.aggregate(np.all)

    bad_comps = set(is_all_good["star_id"][~is_all_good["good"]])

    # Check whether any of the comp stars have NaN values and,
    # if they do, exclude them from the comp set.
    check_for_nan = Table(
        data=[star_data[star_id_column].data, star_data[counts_column_name].data],
        names=["star_id", "net_counts"],
    )
    check_for_nan = check_for_nan.group_by("star_id")
    check_for_nan["good"] = ~np.isnan(check_for_nan["net_counts"])
    is_all_good = check_for_nan.groups.aggregate(np.all)

    bad_comps = bad_comps | set(is_all_good["star_id"][~is_all_good["good"]])

    for comp in bad_comps:
        this_comp = star_data[star_id_column] == comp
        good[this_comp] = False

    error_column_name = "noise_electrons"
    # Calculate comp star counts for each time

    # Make a small table with just counts, errors and time for all of the comparison
    # stars.

    comp_fluxes = star_data["date-obs", counts_column_name, error_column_name][good]
    # Convert comp_fluxes to a regular Table, not a QTable, to work around
    # https://github.com/astropy/astropy/issues/10944
    # in which it was reported that QTable columns with units cannot be aggregated.

    comp_fluxes = Table(comp_fluxes)

    # Check whether any of the columns are masked, but with no masked values,
    # and convert to regular column...eventually

    comp_fluxes = comp_fluxes.group_by("date-obs")
    comp_totals = comp_fluxes.groups.aggregate(np.sum)[counts_column_name]
    comp_num_stars = comp_fluxes.groups.aggregate(np.count_nonzero)[counts_column_name]
    comp_errors = comp_fluxes.groups.aggregate(add_in_quadrature)[error_column_name]

    comp_total_vector = np.ones_like(star_data[counts_column_name])
    comp_error_vector = np.ones_like(star_data[error_column_name])

    if len(set(comp_num_stars)) > 1:
        raise RuntimeError("Different number of stars in comparison sets")

    # Calculate relative flux for every star

    # Have to remove the flux of the star if the star is a comparison
    # star.
    # Use the .value below so that we can set the array to 1 and multiply
    # by it without affecting units of the result.
    is_comp = np.zeros_like(star_data[counts_column_name]).value
    is_comp[good] = 1
    flux_offset = -star_data[counts_column_name] * is_comp

    # Convert comp_fluxes back to a QTable and redo groups
    comp_fluxes = QTable(comp_fluxes)
    comp_fluxes = comp_fluxes.group_by("date-obs")
    # This seems a little hacky; there must be a better way
    for date_obs, comp_total, comp_error in zip(
        comp_fluxes.groups.keys, comp_totals, comp_errors, strict=True
    ):
        this_time = star_data["date-obs"] == date_obs[0]
        comp_total_vector[this_time] *= comp_total
        comp_error_vector[this_time] = comp_error * comp_fluxes[error_column_name].unit

    relative_flux = star_data[counts_column_name] / (comp_total_vector + flux_offset)
    relative_flux = relative_flux.flatten()

    rel_flux_error = (
        star_data[counts_column_name]
        / comp_total_vector
        * np.sqrt(
            (star_data[error_column_name] / star_data[counts_column_name]) ** 2
            + (comp_error_vector / comp_total_vector) ** 2
        )
    )

    # Add these columns to table
    if not in_place:
        star_data = star_data.copy()

    star_data["relative_flux"] = relative_flux
    star_data["relative_flux_error"] = rel_flux_error
    star_data["relative_flux_snr"] = relative_flux / rel_flux_error

    # AIJ records the total comparison counts even though that total is used
    # only for the targets, not the comparison.
    star_data["comparison counts"] = comp_total_vector  # + flux_offset
    star_data["comparison error"] = comp_error_vector

    return star_data


def add_relative_flux_column(
    photometry_data_file,
    source_list_file,
    add_name="-relative-flux",
    verbose=False,
):
    """
    Add AIJ-style relative flux columns to a photometry data file.

    Parameters
    ----------

    photometry_data_file : str
        Path to the photometry data file.

    source_list_file : str
        Path to the source list file.

    add_name : str,  optional
        String to add to the end of the new file name before the suffix.

    Returns
    -------

    None; writes a file with the relative flux columns added.
    """
    if verbose:
        print("Reading photometry data and source list")
    photometry_data = PhotometryData.read(photometry_data_file)
    source_list = SourceListData.read(source_list_file)
    output_file = photometry_data_file.stem + add_name + photometry_data_file.suffix
    source_list["coord"] = SkyCoord(
        ra=source_list["ra"], dec=source_list["dec"], frame="icrs"
    )
    comp_bool = source_list["marker name"] == ["APASS comparison"]
    only_comp_stars = source_list[comp_bool]
    if verbose:
        print("Adding AIJ-style relative flux columns to photomotry data")
    flux_table = calc_aij_relative_flux(photometry_data, only_comp_stars)
    # Add bjd if needed

    if "bjd" not in flux_table.colnames:
        if verbose:
            print("Adding BJD column to photometry data")
        # Accumulate the BJD here
        bjds = []

        flux_group = flux_table.group_by("file")
        for group in flux_group.groups:
            mean_ra = group["ra"].mean()
            mean_dec = group["dec"].mean()
            group.add_bjd_col(bjd_coordinates=SkyCoord(mean_ra, mean_dec))
            bjds.extend(group["bjd"].jd)

    # Each (ephemeral) group had a BJD, this adds the column to the
    # original table.
    flux_group["bjd"] = Time(bjds, scale="tdb", format="jd")

    if verbose:
        print("Writing photometry data with relative flux columns")
    flux_group.write(output_file, overwrite=True)
