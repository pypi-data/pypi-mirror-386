import astropy.units as u
import numpy as np
import pytest
from astropy.coordinates import SkyCoord
from astropy.table import Table
from astropy.time import Time

from stellarphot import PhotometryData
from stellarphot.differential_photometry.aij_rel_fluxes import calc_aij_relative_flux


def _repeat(array, count):
    return np.concatenate([array for _ in range(count)])


def _raw_photometry_table():
    """
    Generate an input raw photometry table and expected flux ratios
    for use in tests.
    """

    n_times = 10
    n_stars = 4
    # How about ten times...
    times = Time("2018-06-25T01:00:00", format="isot", scale="utc")
    times = times + np.arange(n_times) * 30 * u.second
    times = times.value

    # and four stars
    star_ra = 250.0 * u.degree + np.arange(n_stars) * 10 * u.arcmin
    star_dec = np.array([45.0] * n_stars) * u.degree
    fluxes = np.array([10000.0, 20000, 30000, 40000]) * u.adu
    errors = (np.sqrt(fluxes.value) + 50) * u.electron
    star_ids = np.arange(1, 5, dtype="int")

    # Stars 2, 3 and 4 will be the comparison stars
    comp_stars = np.array([0, 1, 1, 1])
    expected_comp_fluxes = np.sum(fluxes[1:])

    comp_flux_offset = -comp_stars * fluxes
    expected_flux_ratios = fluxes / (expected_comp_fluxes + comp_flux_offset)

    comp_error_total = np.sqrt((errors[1:] ** 2).sum())

    expected_flux_error = (
        fluxes
        / expected_comp_fluxes
        * np.sqrt(errors**2 / fluxes**2 + comp_error_total**2 / expected_comp_fluxes**2)
    )

    raw_table = Table(
        data=[
            np.sort(_repeat(times, n_stars)),
            _repeat(star_ra, n_times),
            _repeat(star_dec, n_times),
            _repeat(fluxes, n_times),
            _repeat(errors, n_times),
            _repeat(star_ids, n_times),
        ],
        names=[
            "date-obs",
            "ra",
            "dec",
            "aperture_net_cnts",
            "noise_electrons",
            "star_id",
        ],
        units=[
            None,
            u.degree,
            u.degree,
            u.adu,
            u.electron,
            None,
        ],
    )

    photom = PhotometryData(raw_table)
    # MAKE SURE to return photom, not raw_table, below to trigger the bug
    # https://github.com/feder-observatory/stellarphot/issues/421
    # in which, it turns out, QTable columns with units cannot be aggregated.
    return expected_flux_ratios, expected_flux_error, photom, photom[1:4]


@pytest.mark.parametrize("comp_ra_dec_have_units", [True, False])
@pytest.mark.parametrize("star_ra_dec_have_units", [True, False])
@pytest.mark.parametrize("in_place", [True, False])
def test_relative_flux_calculation(
    in_place, star_ra_dec_have_units, comp_ra_dec_have_units
):
    # In addition to checking the flux calculation values, this is also a regression
    # test for #421.
    expected_flux, expected_error, input_table, comp_star = _raw_photometry_table()

    # Try doing it all at once
    n_times = len(np.unique(input_table["date-obs"]))
    all_expected_flux = _repeat(expected_flux, n_times)
    all_expected_error = _repeat(expected_error, n_times)

    if not star_ra_dec_have_units:
        input_table["ra"] = input_table["ra"].data
        input_table["dec"] = input_table["dec"].data

    if not comp_ra_dec_have_units:
        comp_star["ra"] = comp_star["ra"].data
        comp_star["dec"] = comp_star["dec"].data

    output_table = calc_aij_relative_flux(input_table, comp_star, in_place=in_place)
    output_flux = output_table["relative_flux"]
    output_error = output_table["relative_flux_error"]

    np.testing.assert_allclose(output_flux, all_expected_flux)
    np.testing.assert_allclose(output_error, all_expected_error)
    if in_place:
        assert "relative_flux" in input_table.colnames
    else:
        assert "relative_flux" not in input_table.colnames


@pytest.mark.parametrize("bad_thing", ["RA", "NaN"])
def test_bad_comp_star(bad_thing):
    expected_flux, expected_error, input_table, comp_star = _raw_photometry_table()
    # We'll do modify the "bad" property for the last star in the last
    # image.

    # First, let's sort so the row we want to modify is the last one
    input_table.sort(["date-obs", "star_id"])

    # Force a copy of this row so we have access to the original values
    last_one = Table(input_table[-1])

    if bad_thing == "RA":
        # "Jiggle" one of the stars by moving it by a few arcsec in one image.
        coord_inp = SkyCoord(
            ra=last_one["ra"][0], dec=last_one["dec"][0], unit=u.degree
        )
        coord_bad_ra = coord_inp.ra + 3 * u.arcsecond
        input_table["ra"][-1] = coord_bad_ra
    elif bad_thing == "NaN":
        input_table["aperture_net_cnts"][-1] = np.nan

    output_table = calc_aij_relative_flux(input_table, comp_star, in_place=False)

    old_total_flux = comp_star["aperture_net_cnts"].sum()
    new_flux = old_total_flux - last_one["aperture_net_cnts"]
    # This works for target stars, i.e. those never in comparison set
    new_expected_flux = old_total_flux / new_flux * expected_flux

    # Oh wow, this is terrible....
    # Need to manually calculate for the only two that are still in comparison
    new_expected_flux[1] = (
        comp_star["aperture_net_cnts"][0] / comp_star["aperture_net_cnts"][1]
    )
    new_expected_flux[2] = (
        comp_star["aperture_net_cnts"][1] / comp_star["aperture_net_cnts"][0]
    )

    new_expected_flux[3] = expected_flux[3]
    if bad_thing == "NaN":
        new_expected_flux[3] = np.nan

    np.testing.assert_allclose(new_expected_flux, output_table["relative_flux"][-4:])
