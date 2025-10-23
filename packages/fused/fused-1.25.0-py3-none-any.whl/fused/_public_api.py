from __future__ import annotations

from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Sequence,
)

if TYPE_CHECKING:
    import geopandas as gpd
    import pandas as pd

from fused._global_api import get_api
from fused.core import load_udf_from_code
from fused.models.api import (
    GeospatialPartitionJobStepConfig,
    NonGeospatialPartitionJobStepConfig,
)
from fused.models.api.job import GDALOpenConfig
from fused.models.schema import Schema


def ingest(
    input: str | Path | Sequence[str | Path] | gpd.GeoDataFrame,
    output: str | None = None,
    *,
    output_metadata: str | None = None,
    schema: Schema | None = None,
    file_suffix: str | None = None,
    load_columns: Sequence[str] | None = None,
    remove_cols: Sequence[str] | None = None,
    explode_geometries: bool = False,
    drop_out_of_bounds: bool | None = None,
    partitioning_method: Literal["area", "length", "coords", "rows"] = "rows",
    partitioning_maximum_per_file: int | float | None = None,
    partitioning_maximum_per_chunk: int | float | None = None,
    partitioning_max_width_ratio: int | float = 2,
    partitioning_max_height_ratio: int | float = 2,
    partitioning_force_utm: Literal["file", "chunk", None] = "chunk",
    partitioning_split_method: Literal["mean", "median"] = "mean",
    subdivide_method: Literal["area", None] = None,
    subdivide_start: float | None = None,
    subdivide_stop: float | None = None,
    split_identical_centroids: bool = True,
    target_num_chunks: int = 500,
    lonlat_cols: tuple[str, str] | None = None,
    partitioning_schema_input: str | pd.DataFrame | None = None,
    gdal_config: GDALOpenConfig | dict[str, Any] | None = None,
    overwrite: bool = False,
    as_udf: bool = False,
) -> GeospatialPartitionJobStepConfig:
    """Ingest a dataset into the Fused partitioned format.

    Args:
        input: A GeoPandas `GeoDataFrame` or a path to file or files on S3 to ingest. Files may be Parquet or another geo data format.
        output: Location on S3 to write the `main` table to.
        output_metadata: Location on S3 to write the `fused` table to.
        schema: Schema of the data to be ingested. This is optional and will be inferred from the data if not provided.
        file_suffix: filter which files are used for ingestion. If `input` is a directory on S3, all files under that directory will be listed and used for ingestion. If `file_suffix` is not None, it will be used to filter paths by checking the trailing characters of each filename. E.g. pass `file_suffix=".geojson"` to include only GeoJSON files inside the directory.
        load_columns: Read only this set of columns when ingesting geospatial datasets. Defaults to all columns.
        remove_cols: The named columns to drop when ingesting geospatial datasets. Defaults to not drop any columns.
        explode_geometries: Whether to unpack multipart geometries to single geometries when ingesting geospatial datasets, saving each part as its own row. Defaults to `False`.
        drop_out_of_bounds: Whether to drop geometries outside of the expected WGS84 bounds. Defaults to True.
        partitioning_method: The method to use for grouping rows into partitions. Defaults to `"rows"`.

            - `"area"`: Construct partitions where all contain a maximum total area among geometries.
            - `"length"`: Construct partitions where all contain a maximum total length among geometries.
            - `"coords"`: Construct partitions where all contain a maximum total number of coordinates among geometries.
            - `"rows"`: Construct partitions where all contain a maximum number of rows.

        partitioning_maximum_per_file: Maximum value for `partitioning_method` to use per file. If `None`, defaults to _1/10th_ of the total value of `partitioning_method`. So if the value is `None` and `partitioning_method` is `"area"`, then each file will have no more than 1/10th the total area of all geometries. Defaults to `None`.
        partitioning_maximum_per_chunk: Maximum value for `partitioning_method` to use per chunk. If `None`, defaults to _1/100th_ of the total value of `partitioning_method`. So if the value is `None` and `partitioning_method` is `"area"`, then each file will have no more than 1/100th the total area of all geometries. Defaults to `None`.
        partitioning_max_width_ratio: The maximum ratio of width to height of each partition to use in the ingestion process. So for example, if the value is `2`, then if the width divided by the height is greater than `2`, the box will be split in half along the horizontal axis. Defaults to `2`.
        partitioning_max_height_ratio: The maximum ratio of height to width of each partition to use in the ingestion process. So for example, if the value is `2`, then if the height divided by the width is greater than `2`, the box will be split in half along the vertical axis. Defaults to `2`.
        partitioning_force_utm: Whether to force partitioning within UTM zones. If set to `"file"`, this will ensure that the centroid of all geometries per _file_ are contained in the same UTM zone. If set to `"chunk"`, this will ensure that the centroid of all geometries per _chunk_ are contained in the same UTM zone. If set to `None`, then no UTM-based partitioning will be done. Defaults to "chunk".
        partitioning_split_method: How to split one partition into children. Defaults to `"mean"` (this may change in the future).

            - `"mean"`: Split each axis according to the mean of the centroid values.
            - `"median"`: Split each axis according to the median of the centroid values.

        subdivide_method: The method to use for subdividing large geometries into multiple rows. Currently the only option is `"area"`, where geometries will be subdivided based on their area (in WGS84 degrees).
        subdivide_start: The value above which geometries will be subdivided into smaller parts, according to `subdivide_method`.
        subdivide_stop: The value below which geometries will not be subdivided into smaller parts, according to `subdivide_method`. Recommended to be equal to subdivide_start. If `None`, geometries will be subdivided up to a recursion depth of 100 or until the subdivided geometry is rectangular.
        split_identical_centroids: If `True`, should split a partition that has
            identical centroids (such as if all geometries in the partition are the
            same) if there are more such rows than defined in "partitioning_maximum_per_file" and
            "partitioning_maximum_per_chunk".
        target_num_chunks: The target for the number of files if `partitioning_maximum_per_file` is None. Note that this number is only a _target_ and the actual number of files generated can be higher or lower than this number, depending on the spatial distribution of the data itself.
            Defaults to 500, rough default to use in most cases.
        lonlat_cols: Names of longitude, latitude columns to construct point geometries from.

            If your point columns are named `"x"` and `"y"`, then pass:

            ```py
            fused.ingest(
                ...,
                lonlat_cols=("x", "y")
            )
            ```

            This only applies to reading from Parquet files. For reading from CSV files, pass options to `gdal_config`.

        gdal_config: Configuration options to pass to GDAL for how to read these files. For all files other than Parquet files, Fused uses GDAL as a step in the ingestion process. For some inputs, like CSV files or zipped shapefiles, you may need to pass some parameters to GDAL to tell it how to open your files.

            This config is expected to be a dictionary with up to two keys:

            - `layer`: `str`. Define the layer of the input file you wish to read when the source contains multiple layers, as in GeoPackage.
            - `open_options`: `Dict[str, str]`. Pass in key-value pairs with GDAL open options. These are defined on each driver's page in the GDAL documentation. For example, the [CSV driver](https://gdal.org/drivers/vector/csv.html) defines [these open options](https://gdal.org/drivers/vector/csv.html#open-options) you can pass in.

            For example, if you're ingesting a CSV file with two columns
            `"longitude"` and `"latitude"` denoting the coordinate information, pass

            ```py
            fused.ingest(
                ...,
                gdal_config={
                    "open_options": {
                        "X_POSSIBLE_NAMES": "longitude",
                        "Y_POSSIBLE_NAMES": "latitude",
                    }
                }
            )
            ```
        overwrite: If True, overwrite the output directory if it already exists
            (by first removing all existing content of the directory, i.e. it
            does not only overwrite conflicting files).
            Defaults to False.
        as_udf: Return the ingestion workflow as a UDF that can be executed using
            `fused.run()`. Local files or python objects passed to `input` or
            `partitioning_schema_input` are still uploaded to S3 first such that
            those are available when executing the UDF remotely. Defaults to False.

    Returns:
        Configuration object describing the ingestion process. Call `.execute` on this object to start a job.

    Examples:
        For example, to ingest the California Census dataset for the year 2022:
        ```py
        job = fused.ingest(
            input="https://www2.census.gov/geo/tiger/TIGER_RD18/STATE/06_CALIFORNIA/06/tl_rd22_06_bg.zip",
            output="s3://fused-sample/census/ca_bg_2022/main/",
            output_metadata="s3://fused-sample/census/ca_bg_2022/fused/",
            explode_geometries=True,
            partitioning_maximum_per_file=2000,
            partitioning_maximum_per_chunk=200,
        ).execute()
        ```
    """
    remove_cols = remove_cols if remove_cols else []
    if (
        subdivide_start is not None or subdivide_stop is not None
    ) and subdivide_method is None:
        raise ValueError(
            'subdivide_start or subdivide_stop require subdivide_method be specified (it should be "area")'
        )
    api = get_api()
    input = api._upload_local_input(input)
    if partitioning_schema_input is not None:
        partitioning_schema_input = api._upload_local_input(partitioning_schema_input)

    if as_udf:
        if schema is not None:
            raise ValueError(
                "The `schema` argument is not yet supported when `as_udf=True`. "
                "The schema will be inferred from the input data."
            )
        template = f"""\
@fused.udf
def udf():
    try:
        from job2.api import run_partition_input_for_udf
    except ImportError:
        raise RuntimeError(
            "The ingestion UDF can only be run using the remote engine"
        )

    from fused.models.api import GeospatialPartitionJobStepConfig

    config = GeospatialPartitionJobStepConfig(
        input={input!r},
        output={output!r},
        output_metadata={output_metadata!r},
        file_suffix={file_suffix!r},
        load_columns={load_columns!r},
        remove_cols={remove_cols!r},
        explode_geometries={explode_geometries!r},
        drop_out_of_bounds={drop_out_of_bounds!r},
        lonlat_cols={lonlat_cols!r},
        partitioning_maximum_per_file={partitioning_maximum_per_file!r},
        partitioning_maximum_per_chunk={partitioning_maximum_per_chunk!r},
        partitioning_max_width_ratio={partitioning_max_width_ratio!r},
        partitioning_max_height_ratio={partitioning_max_height_ratio!r},
        partitioning_method={partitioning_method!r},
        partitioning_force_utm={partitioning_force_utm!r},
        partitioning_split_method={partitioning_split_method!r},
        subdivide_start={subdivide_start!r},
        subdivide_stop={subdivide_stop!r},
        subdivide_method={subdivide_method!r},
        split_identical_centroids={split_identical_centroids!r},
        target_num_chunks={target_num_chunks!r},
        partitioning_schema_input={partitioning_schema_input!r},
        # TODO support gdal_config
        overwrite={overwrite!r},
    )
    run_partition_input_for_udf(config)
"""
        udf = load_udf_from_code(template)
        return udf

    return GeospatialPartitionJobStepConfig(
        input=input,
        output=output,
        output_metadata=output_metadata,
        table_schema=schema,
        file_suffix=file_suffix,
        load_columns=load_columns,
        remove_cols=remove_cols,
        explode_geometries=explode_geometries,
        drop_out_of_bounds=drop_out_of_bounds,
        lonlat_cols=lonlat_cols,
        partitioning_maximum_per_file=partitioning_maximum_per_file,
        partitioning_maximum_per_chunk=partitioning_maximum_per_chunk,
        partitioning_max_width_ratio=partitioning_max_width_ratio,
        partitioning_max_height_ratio=partitioning_max_height_ratio,
        partitioning_method=partitioning_method,
        partitioning_force_utm=partitioning_force_utm,
        partitioning_split_method=partitioning_split_method,
        subdivide_start=subdivide_start,
        subdivide_stop=subdivide_stop,
        subdivide_method=subdivide_method,
        split_identical_centroids=split_identical_centroids,
        target_num_chunks=target_num_chunks,
        partitioning_schema_input=partitioning_schema_input,
        gdal_config=GDALOpenConfig() if gdal_config is None else gdal_config,
        overwrite=overwrite,
    )


def ingest_nongeospatial(
    input: str | Path | Sequence[str, Path] | pd.DataFrame | gpd.GeoDataFrame,
    output: str | None = None,
    *,
    output_metadata: str | None = None,
    partition_col: str | None = None,
    partitioning_maximum_per_file: int = 2_500_000,
    partitioning_maximum_per_chunk: int = 65_000,
) -> NonGeospatialPartitionJobStepConfig:
    """Ingest a dataset into the Fused partitioned format.

    Args:
        input: A GeoPandas `GeoDataFrame` or a path to file or files on S3 to ingest. Files may be Parquet or another geo data format.
        output: Location on S3 to write the `main` table to.
        output_metadata: Location on S3 to write the `fused` table to.
        partition_col: Partition along this column for nongeospatial datasets.
        partitioning_maximum_per_file: Maximum number of items to store in a single file. Defaults to 2,500,000.
        partitioning_maximum_per_chunk: Maximum number of items to store in a single file. Defaults to 65,000.

    Returns:
        Configuration object describing the ingestion process. Call `.execute` on this object to start a job.

    Examples:
        ```py
        job = fused.ingest_nongeospatial(
            input=gdf,
            output="s3://sample-bucket/file.parquet",
        ).execute()
        ```
    """
    api = get_api()
    input = api._upload_local_input(input)
    return NonGeospatialPartitionJobStepConfig(
        input=input,
        output=output,
        output_metadata=output_metadata,
        partition_col=partition_col,
        partitioning_maximum_per_file=partitioning_maximum_per_file,
        partitioning_maximum_per_chunk=partitioning_maximum_per_chunk,
    )
