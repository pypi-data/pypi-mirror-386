import warnings

import ipywidgets as ipw
import numpy as np
from astropy.io import fits
from astropy.table import Table

try:
    from astrowidgets import ImageWidget
except ImportError:
    from astrowidgets.ginga import ImageWidget

import matplotlib.pyplot as plt

from stellarphot.io import TessSubmission
from stellarphot.photometry import CenterAndProfile
from stellarphot.photometry.photometry import EXPOSURE_KEYWORDS
from stellarphot.plotting import seeing_plot
from stellarphot.settings import (
    PartialPhotometrySettings,
    PhotometryApertures,
    PhotometryWorkingDirSettings,
    SavedSettings,
    ui_generator,
)
from stellarphot.settings.custom_widgets import ChooseOrMakeNew
from stellarphot.settings.fits_opener import FitsOpener

__all__ = [
    "set_keybindings",
    "SeeingProfileWidget",
]

DESC_STYLE = {"description_width": "initial"}
AP_SETTING_NEEDS_SAVE = "❗️"
AP_SETTING_SAVED = "✅"
DEFAULT_SAVE_TITLE = "Save aperture and camera"


# TODO: maybe move this into SeeingProfileWidget unless we anticipate
# other widgets using this.
def set_keybindings(image_widget, scroll_zoom=False):
    """
    Set image widget keyboard bindings. The bindings are:

    + Pan by click-and-drag or with arrow keys.
    + Zoom by scrolling or using the ``+``/``-`` keys.
    + Adjust contrast by Ctrl-right click and drag
    + Reset contrast with shift-right-click.

    Any existing key bindings are removed.

    Parameters
    ----------

    image_widget : `astrowidgets.ImageWidget`
        Image widget on which to set the key bindings.

    scroll_zoom : bool, optional
        If True, zooming can be done by scrolling the mouse wheel.
        Default is False.

    Returns
    -------

    None
        Adds key bindings to the image widget.
    """
    bind_map = image_widget._viewer.get_bindmap()
    # Displays the event map...
    # bind_map.eventmap
    bind_map.clear_event_map()
    bind_map.map_event(None, (), "ms_left", "pan")
    if scroll_zoom:
        bind_map.map_event(None, (), "pa_pan", "zoom")

    # bind_map.map_event(None, (), 'ms_left', 'cursor')
    # contrast with right mouse
    bind_map.map_event(None, (), "ms_right", "contrast")

    # shift-right mouse to reset contrast
    bind_map.map_event(None, ("shift",), "ms_right", "contrast_restore")
    bind_map.map_event(None, ("ctrl",), "ms_left", "cursor")

    # Bind +/- to zoom in/out
    bind_map.map_event(None, (), "kp_+", "zoom_in")
    bind_map.map_event(None, (), "kp_=", "zoom_in")
    bind_map.map_event(None, (), "kp_-", "zoom_out")
    bind_map.map_event(None, (), "kp__", "zoom_out")

    # Bind arrow keys to panning
    # There is NOT a typo below. I want the keys to move the image in the
    # direction of the arrow
    bind_map.map_event(None, (), "kp_left", "pan_right")
    bind_map.map_event(None, (), "kp_right", "pan_left")
    bind_map.map_event(None, (), "kp_up", "pan_down")
    bind_map.map_event(None, (), "kp_down", "pan_up")


class SeeingProfileWidget:
    """
    A class for storing an instance of a widget displaying the seeing profile
    of stars in an image.

    Parameters
    ----------
    imagewidget : `astrowidgets.ImageWidget`, optional
        ImageWidget instance to use for the seeing profile.

    width : int, optional
        Width of the seeing profile widget. Default is 500 pixels.

    camera : `stellarphot.settings.Camera`, optional
        Camera instance to use for calculating the signal to noise ratio. If
        ``None``, the signal to noise ratio will not be calculated.

    observatory : `stellarphot.settings.Observatory`, optional
        Observatory instance to use for setting the TESS telescope information.
        If `None`, or if the `~stellarphot.settings.Observatory.TESS_telescope_code`
        is `None`, the TESS settings will not be displayed.

    Attributes
    ----------

    ap_t : `ipywidgets.IntText`
        Text box for the aperture radius.

    box : `ipywidgets.VBox`
        Box containing the seeing profile widget.

    container : `ipywidgets.VBox`
        Container for the seeing profile widget.

    object_name : str
        Name of the object in the FITS file.

    in_t : `ipywidgets.IntText`
        Text box for the inner annulus.

    iw : `astrowidgets.ImageWidget`
        ImageWidget instance used for the seeing profile.

    object_name : str
        Name of the object in the FITS file.

    out : `ipywidgets.Output`
        Output widget for the seeing profile.

    out2 : `ipywidgets.Output`
        Output widget for the integrated counts.

    out3 : `ipywidgets.Output`
        Output widget for the SNR.

    out_t : `ipywidgets.IntText`
        Text box for the outer annulus.

    rad_prof : `RadialProfile`
        Radial profile of the star.

    save_aps : `ipywidgets.Button`
        Button to save the aperture settings.

    tess_box : `ipywidgets.VBox`
        Box containing the TESS settings.

    """

    def __init__(
        self,
        imagewidget=None,
        width=500,
        camera=None,
        observatory=None,
        _testing_path=None,
    ):
        if not imagewidget:
            imagewidget = ImageWidget(
                image_width=width, image_height=width, use_opencv=True
            )

        self.photometry_settings = PhotometryWorkingDirSettings()
        self.iw = imagewidget

        self.observatory = observatory

        # If a camera is provided make sure it has already been saved.
        # If it has not been saved, raise an error.
        if camera is not None:
            saved = SavedSettings(_testing_path=_testing_path)
            if camera not in saved.cameras.as_dict.values():
                saved.add_item(camera)

        # Do some set up of the ImageWidget
        set_keybindings(self.iw, scroll_zoom=False)
        bind_map = self.iw._viewer.get_bindmap()
        bind_map.map_event(None, ("shift",), "ms_left", "cursor")
        gvc = self.iw._viewer.get_canvas()
        self._mse = self._make_show_event()
        gvc.add_callback("cursor-down", self._mse)

        # Outputs to hold the graphs
        self.seeing_profile_plot = ipw.Output()
        self.curve_growth_plot = ipw.Output()
        self.snr_plot = ipw.Output()

        # Include an error console to display messages to the user
        self.error_console = ipw.Output()

        # Build the larger widget
        self.container = ipw.VBox()
        self.fits_file = FitsOpener(title=self._format_title("Choose an image"))
        self.camera_chooser = ChooseOrMakeNew(
            "camera", details_hideable=True, _testing_path=_testing_path
        )

        if camera is not None:
            self.camera_chooser._choose_existing.value = camera

        # Do not show the camera details by default
        self.camera_chooser.display_details = False

        image_camer_box = ipw.HBox()
        image_camer_box.children = [self.fits_file.file_chooser, self.camera_chooser]

        im_view_plot_box = ipw.GridspecLayout(1, 2)

        # Box for aperture settings and title
        ap_setting_box = ipw.VBox()

        self.ap_title = ipw.HTML(value=self._format_title(DEFAULT_SAVE_TITLE))
        self.aperture_settings = ui_generator(PhotometryApertures)
        self.aperture_settings.show_savebuttonbar = True
        self.aperture_settings.savebuttonbar.fns_onsave_add_action(self.save)

        ap_setting_box.children = [
            self.ap_title,
            self.aperture_settings,
        ]

        plot_box = ipw.VBox()
        plt_tabs = ipw.Tab()
        plt_tabs.children = [
            self.snr_plot,
            self.seeing_profile_plot,
            self.curve_growth_plot,
        ]
        plt_tabs.titles = [
            "SNR",
            "Seeing profile",
            "Integrated counts",
        ]

        self.tess_box = self._make_tess_box()
        plot_box.children = [plt_tabs, self.tess_box]

        imbox = ipw.VBox()
        imbox.children = [imagewidget]
        im_view_plot_box[0, 0] = imbox
        im_view_plot_box[0, 1] = plot_box
        im_view_plot_box.layout.width = "100%"

        # Line below puts space between the image and the plots so the plots
        # don't jump around as the image value changes.
        im_view_plot_box.layout.justify_content = "space-between"
        self.big_box = im_view_plot_box
        self.container.children = [
            image_camer_box,
            self.error_console,
            self.big_box,
            ap_setting_box,
        ]
        self.box = self.container
        self._aperture_name = "aperture"

        self._tess_sub = None

        # This is eventually used to store the radial profile
        self.rad_prof = None
        # Fill these in later with name of object from FITS file
        self.object_name = ""
        self.exposure = 0
        self._set_observers()
        self.aperture_settings.description = ""

    @property
    def camera(self):
        return self.camera_chooser.value

    def load_fits(self):
        """
        Load a FITS file into the image widget.
        """
        self.fits_file.load_in_image_widget(self.iw)
        self.object_name = self.fits_file.object
        for key in EXPOSURE_KEYWORDS:
            if key in self.fits_file.header:
                self.exposure = self.fits_file.header[key]
                break
        else:
            # apparently setting a higher stacklevel is better, see
            # https://docs.astral.sh/ruff/rules/no-explicit-stacklevel/
            warnings.warn(
                "No exposure time keyword found in FITS header. "
                "Setting exposure to NaN",
                stacklevel=2,
            )
            self.exposure = np.nan

    def save(self):
        """
        Save all of the settings we have to a partial settings file.
        """
        self.photometry_settings.save(
            PartialPhotometrySettings(
                photometry_apertures=self.aperture_settings.value, camera=self.camera
            ),
            update=True,
        )

        # For some reason the value of unsaved_changes is not updated until after this
        # function executes, so we force its value here.
        self.aperture_settings.savebuttonbar.unsaved_changes = False
        # Update the save box title to reflect the save
        self._set_save_box_title("")

    def _format_title(self, title):
        """
        Format titles in a consistent way.
        """
        return f"<h2>{title}</h2>"

    def _update_file(self, change):  # noqa: ARG002
        # Widget callbacks need to accept a single argument, even if it is not used.
        self.load_fits()

    def _construct_tess_sub(self):
        file = self.fits_file.path
        self._tess_sub = TessSubmission.from_header(
            fits.getheader(file),
            telescope_code=self.setting_box.telescope_code.value,
            planet=self.setting_box.planet_num.value,
        )

    def _set_seeing_profile_name(self, change):  # noqa: ARG002
        """
        Widget callbacks need to accept a single argument, even if it is not used.
        """
        self._construct_tess_sub()
        self.seeing_file_name.value = self._tess_sub.seeing_profile

    def _save_toggle_action(self, change):
        activated = change["new"]

        if activated:
            self.setting_box.layout.visibility = "visible"
            self._set_seeing_profile_name("")
        else:
            self.setting_box.layout.visibility = "hidden"

    def _save_seeing_plot(self, button):  # noqa: ARG002
        """
        Widget button callbacks need to accept a single argument.
        """
        self._seeing_plot_fig.savefig(self.seeing_file_name.value)

    def _set_save_box_title(self, change):
        # If we got here via a traitlets event then change is a dict, check that
        # case first.
        dirty = False

        try:
            if change["new"] != change["old"]:
                dirty = True
        except (KeyError, TypeError):
            dirty = False

        # The unsaved_changes attribute is not a traitlet, and it isn't clear when
        # in the event handling it gets set. When not called from an event, though,
        # this function can only used unsaved_changes to decide what the title
        # should be.
        if self.aperture_settings.savebuttonbar.unsaved_changes or dirty:
            self.ap_title.value = self._format_title(
                f"{DEFAULT_SAVE_TITLE} {AP_SETTING_NEEDS_SAVE}"
            )
        else:
            self.ap_title.value = self._format_title(
                f"{DEFAULT_SAVE_TITLE} {AP_SETTING_SAVED}"
            )

    def _set_observers(self):
        def aperture_obs(change):
            self._update_plots()
            ape = PhotometryApertures(**change["new"])
            self.aperture_settings.description = (
                f"Aperture radius: {ape.radius_pixels(ape.fwhm_estimate):.2f} pix, "
                f"Inner annulus: {ape.inner_annulus:.2f} pix, "
                f"outer annulus: {ape.outer_annulus:.2f} pix"
            )

        self.aperture_settings.observe(aperture_obs, names="_value")

        self.fits_file.file_chooser.observe(self._update_file, names="_value")

        self.aperture_settings.observe(self._set_save_box_title, "_value")

        if self.save_toggle:
            self.save_toggle.observe(self._save_toggle_action, names="value")
            self.save_seeing.on_click(self._save_seeing_plot)
            self.setting_box.planet_num.observe(self._set_seeing_profile_name)
            self.setting_box.telescope_code.observe(self._set_seeing_profile_name)

    def _make_tess_box(self):
        box = ipw.VBox()

        if self.observatory is None or self.observatory.TESS_telescope_code is None:
            """
            No TESS information, so definitely don't display this group of settings.
            """
            box.layout.flex_flow = "row wrap"
            box.layout.visibility = "hidden"

            self.save_toggle = None
            return box

        setting_box = ipw.HBox()
        self.save_toggle = ipw.ToggleButton(
            description="TESS seeing profile...", disabled=True
        )
        scope_name = ipw.Text(
            description="Telescope code",
            value=self.observatory.TESS_telescope_code,
            style=DESC_STYLE,
        )
        planet_num = ipw.IntText(description="Planet", value=1)
        self.save_seeing = ipw.Button(description="Save")
        self.seeing_file_name = ipw.Label(value="Moo")
        setting_box.children = (
            scope_name,
            planet_num,
            self.seeing_file_name,
            self.save_seeing,
        )
        # for kid in setting_box.children:
        #     kid.disabled = True
        box.children = (self.save_toggle, setting_box)
        setting_box.telescope_code = scope_name
        setting_box.planet_num = planet_num
        setting_box.layout.flex_flow = "row wrap"
        setting_box.layout.visibility = "hidden"
        self.setting_box = setting_box
        return box

    def _update_ap_settings(self, value):
        self.aperture_settings.value = value

    def _make_show_event(self):
        def show_event(
            viewer, event=None, datax=None, datay=None, aperture=None  # noqa: ARG001
        ):
            """
            ginga callbacks require the function signature above.
            """
            profile_size = 60
            centering_cutout_size = 20
            default_gap = 5  # pixels
            default_annulus_width = 15  # pixels
            if self.save_toggle:
                self.save_toggle.disabled = False

            update_aperture_settings = False
            if event is not None:
                # User clicked on a star, so generate profile
                i = self.iw._viewer.get_image()
                data = i.get_data()

                # Rough location of click in original image
                x = int(np.floor(event.data_x))
                y = int(np.floor(event.data_y))

                try:
                    rad_prof = CenterAndProfile(
                        data,
                        (x, y),
                        profile_radius=profile_size,
                        centering_cutout_size=centering_cutout_size,
                    )
                except RuntimeError as e:
                    # Check whether this error is one generated by RadialProfile
                    if "Centroid did not converge on a star." in str(e):
                        # Clear any previous messages...no idea why the clear_output
                        # method doesn't work here, but it doesn't/
                        self.error_console.outputs = ()

                        # Use the append_display_data method instead of the
                        # error_console context manager because there seems to be
                        # a timing issue with the context manager when running
                        # tests.
                        self.error_console.append_display_data(
                            ipw.HTML(
                                "<strong>No star found at this location. "
                                "Try clicking closer "
                                "to a star or on a brighter star</strong>"
                            )
                        )
                        print(f"{self.error_console.outputs=}")
                        return
                    else:
                        # RadialProfile did not generate this error, pass it
                        # on to the user
                        raise e  # pragma: no cover
                else:
                    # Success, clear any previous error messages
                    self.error_console.clear_output()

                try:
                    try:  # Remove previous marker
                        self.iw.remove_markers(marker_name=self._aperture_name)
                    except AttributeError:
                        self.iw.remove_markers_by_name(marker_name=self._aperture_name)
                except ValueError:
                    # No markers yet, keep going
                    pass

                # ADD MARKER WHERE CLICKED
                self.iw.add_markers(
                    Table(
                        data=[[rad_prof.center[0]], [rad_prof.center[1]]],
                        names=["x", "y"],
                    ),
                    marker_name=self._aperture_name,
                )

                # Default is 1.5 times FWHM
                aperture_radius = np.round(1.5 * rad_prof.FWHM, 0)
                self.rad_prof = rad_prof

                # Make an aperture settings object, but don't update it's widget yet.
                ap_settings = PhotometryApertures(
                    radius=aperture_radius,
                    gap=default_gap,
                    annulus_width=default_annulus_width,
                    fwhm_estimate=rad_prof.FWHM,
                )
                update_aperture_settings = True
            else:
                # User changed aperture
                aperture_radius = aperture["radius"]
                ap_settings = PhotometryApertures(
                    **aperture
                )  # Make an aperture settings object, but don't update it's widget yet.

            if update_aperture_settings:
                # So it turns out that the validation stuff only updates when changes
                # are made in the UI rather than programmatically. Since we know we've
                # set a valid value, and that we've made changes we just manually set
                # the relevant values.
                self.aperture_settings.savebuttonbar.unsaved_changes = True
                self.aperture_settings.is_valid.value = True

                # Update the value last so that the unsaved state is properly set when
                # the value is updated.
                self._update_ap_settings(ap_settings.model_dump())

            self._update_plots()

        return show_event

    def _update_plots(self):
        # DISPLAY THE SCALED PROFILE
        fig_size = (10, 5)

        # Stop if the update is happening before a radial profile has been generated
        # (e.g. the user changes the aperture settings before loading an image).
        if self.rad_prof is None:
            return

        rad_prof = self.rad_prof
        self.seeing_profile_plot.clear_output(wait=True)
        ap_settings = PhotometryApertures(**self.aperture_settings.value)
        with self.seeing_profile_plot:
            r_exact, individual_counts = rad_prof.pixel_values_in_profile
            scaled_exact_counts = (
                individual_counts / rad_prof.radial_profile.profile.max()
            )
            self._seeing_plot_fig = seeing_plot(
                r_exact,
                scaled_exact_counts,
                rad_prof.radial_profile.radius,
                rad_prof.normalized_profile,
                rad_prof.HWHM,
                self.object_name,
                photometry_settings=ap_settings,
                figsize=fig_size,
            )
            plt.show()

        # CALCULATE AND DISPLAY NET COUNTS INSIDE RADIUS
        self.curve_growth_plot.clear_output(wait=True)
        with self.curve_growth_plot:
            cog = rad_prof.curve_of_growth

            plt.figure(figsize=fig_size)
            plt.plot(cog.radius, cog.profile)
            plt.xlim(0, 40)
            ylim = plt.ylim()
            plt.vlines(
                ap_settings.radius_pixels(rad_prof.FWHM), *plt.ylim(), colors=["red"]
            )
            plt.ylim(*ylim)
            plt.grid()

            plt.title("Net counts in aperture")

            plt.xlabel("Aperture radius (pixels)")
            plt.ylabel(f"Net counts ({self.camera.data_unit})")
            plt.show()

        # CALCULATE And DISPLAY SNR AS A FUNCTION OF RADIUS
        self.snr_plot.clear_output(wait=True)
        with self.snr_plot:
            plt.figure(figsize=fig_size)
            snr = rad_prof.snr(self.camera, self.exposure)

            plt.plot(rad_prof.curve_of_growth.radius, snr)

            plt.title(
                f"Signal to noise ratio max {snr.max():.1f} "
                f"at radius {snr.argmax() + 1}"
            )
            plt.xlim(0, 40)
            ylim = plt.ylim()
            plt.vlines(
                ap_settings.radius_pixels(rad_prof.FWHM), *plt.ylim(), colors=["red"]
            )
            plt.ylim(*ylim)
            plt.xlabel("Aperture radius (pixels)")
            plt.ylabel("SNR")
            plt.grid()
            plt.show()
