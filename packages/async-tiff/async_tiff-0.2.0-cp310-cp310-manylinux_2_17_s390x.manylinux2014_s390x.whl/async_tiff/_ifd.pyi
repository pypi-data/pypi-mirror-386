from .enums import (
    CompressionMethod,
    PhotometricInterpretation,
    PlanarConfiguration,
    Predictor,
    ResolutionUnit,
    SampleFormat,
)
from ._geo import GeoKeyDirectory

Value = int | float | str | tuple[int, int] | list[Value]

class ImageFileDirectory:
    @property
    def new_subfile_type(self) -> int | None: ...
    @property
    def image_width(self) -> int:
        """The number of columns in the image, i.e., the number of pixels per row."""

    @property
    def image_height(self) -> int:
        """The number of rows of pixels in the image."""

    @property
    def bits_per_sample(self) -> list[int]: ...
    @property
    def compression(self) -> CompressionMethod | int:
        """Access the compression tag.

        An `int` will be returned if the compression is not one of the values in
        `CompressionMethod`.
        """
    @property
    def photometric_interpretation(self) -> PhotometricInterpretation: ...
    @property
    def document_name(self) -> str | None: ...
    @property
    def image_description(self) -> str | None: ...
    @property
    def strip_offsets(self) -> list[int] | None: ...
    @property
    def orientation(self) -> int | None: ...
    @property
    def samples_per_pixel(self) -> int:
        """
        The number of components per pixel.

        SamplesPerPixel is usually 1 for bilevel, grayscale, and palette-color images.
        SamplesPerPixel is usually 3 for RGB images. If this value is higher,
        ExtraSamples should give an indication of the meaning of the additional
        channels.
        """

    @property
    def rows_per_strip(self) -> int | None: ...
    @property
    def strip_byte_counts(self) -> int | None: ...
    @property
    def min_sample_value(self) -> int | None: ...
    @property
    def max_sample_value(self) -> int | None: ...
    @property
    def x_resolution(self) -> float | None:
        """The number of pixels per ResolutionUnit in the ImageWidth direction."""

    @property
    def y_resolution(self) -> float | None:
        """The number of pixels per ResolutionUnit in the ImageLength direction."""

    @property
    def planar_configuration(self) -> PlanarConfiguration: ...
    @property
    def resolution_unit(self) -> ResolutionUnit | None: ...
    @property
    def software(self) -> str | None: ...
    @property
    def date_time(self) -> str | None: ...
    @property
    def artist(self) -> str | None: ...
    @property
    def host_computer(self) -> str | None: ...
    @property
    def predictor(self) -> Predictor | None: ...
    @property
    def tile_width(self) -> int | None: ...
    @property
    def tile_height(self) -> int | None: ...
    @property
    def tile_offsets(self) -> list[int] | None: ...
    @property
    def tile_byte_counts(self) -> list[int] | None: ...
    @property
    def extra_samples(self) -> list[int] | None: ...
    @property
    def sample_format(self) -> list[SampleFormat]: ...
    @property
    def jpeg_tables(self) -> bytes | None: ...
    @property
    def copyright(self) -> str | None: ...
    @property
    def geo_key_directory(self) -> GeoKeyDirectory | None: ...
    @property
    def model_pixel_scale(self) -> list[float] | None: ...
    @property
    def model_tiepoint(self) -> list[float] | None: ...
    @property
    def other_tags(self) -> dict[int, Value]: ...
