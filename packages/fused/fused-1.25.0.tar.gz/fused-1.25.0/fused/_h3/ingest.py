import fused


def run_ingest_tiff_to_h3(
    tiff_path: str,
    output_path: str,
    target_chunk_size: int = 10_000_000,
    # instance_type: str = "small",
    res: int = 12,  # or 11 ?
    k_ring: int = 1,
    parent_offset: int = 1,
    base_res: int = 7,
    chunk_res: int = 3,
    file_res: int = 2,
    ops=["divide", "combine", "sample"],
    # n_jobs_divide=20,
    # n_jobs_combine=5,
    debug_mode: bool = False,
    remove_tmp_files: bool = True,
    cache_id: int = 0,
    divide_kwargs={},
    combine_kwargs={},
    **kwargs,
):
    """
    Chunk up the input TIFF file, extract pixel values and assign to H3 cells.

    Parameters
    ----------
    tiff_path : str
        Path to the input TIFF file.
    tmp_path : str
        Path to store intermediate files.
    target_chunk_size : int
        The approximate number of pixel values to process per chunk.
    instance_type : str
    res : int
        The resolution at which to assign the pixel values to H3 cells.
    k_ring : int
        The k-ring distance at resolution `res` to which the pixel value
        is assigned (in addition to the center cell).
    parent_offset : int
        Offset to parent resolution to which to assign the pixel values
        and counts
    file_res : int
        The H3 resolution to chunk the resulting files of the Parquet dataset
    base_res : int
        The lowest parent resolution for which to include the hex value in the resulting file.
    chunk_res : int
        The H3 resolution to chunk the row groups within each file of the Parquet dataset

    """
    import datetime

    import numpy as np
    import rasterio

    try:
        from job2.partition.tiff_to_h3 import (
            udf_overview,
            udf_sample,
        )
    except ImportError:
        raise RuntimeError(
            "The ingestion functionality can only be run using the remote engine"
        )

    result_divide = None
    result_combine = None

    print(f"Starting ingestion process for {tiff_path}\n")

    # Construct path for intermediate results
    api = fused.api.FusedAPI()
    tmp_path = api._resolve(
        "fd://fused-tmp/tmp/"
        + tiff_path.replace("/", "_").replace(":", "_").replace(".", "_")
        + f"-{cache_id}/"
    )
    print(f"-- Using {tmp_path=}")

    start_time = datetime.datetime.now()

    ###########################################################################
    # Step one: extracting pixel values and converting to hex divided in chunks

    print("\nRunning divide step")

    @fused.udf(cache_max_age=0)
    def udf_divide(
        tiff_path: str,
        chunk_id: int,
        x_chunks: int,
        y_chunks: int,
        tmp_path: str,
        res: int,
        k_ring: int,
        parent_offset: int,
        file_res: int,
    ):
        # define inline UDF that imports the helper function inside the UDF
        from job2.partition.tiff_to_h3 import udf_divide as run_udf_divide

        run_udf_divide(
            tiff_path,
            chunk_id,
            x_chunks,
            y_chunks,
            tmp_path,
            res=res,
            k_ring=k_ring,
            parent_offset=parent_offset,
            file_res=file_res,
        )

    # determine number of chunks based on target chunk size
    with rasterio.open(tiff_path) as src:
        meta = src.meta

    x_chunks = round(meta["width"] / np.sqrt(target_chunk_size))
    y_chunks = round(meta["height"] / np.sqrt(target_chunk_size))

    params = {
        "tiff_path": tiff_path,
        "tmp_path": tmp_path,
        "x_chunks": x_chunks,
        "y_chunks": y_chunks,
        #
        "res": res,
        "k_ring": k_ring,
        "parent_offset": parent_offset,
        "file_res": file_res,
    }
    submit_params = [{"chunk_id": i} for i in range(x_chunks * y_chunks)]
    if debug_mode:
        submit_params = submit_params[:2]

    result_divide = fused.submit(
        udf_divide,
        submit_params,
        **params,
        collect=False,
        **divide_kwargs,
        **kwargs,
    )
    result_divide.wait()
    end_divide_time = datetime.datetime.now()
    if not result_divide.all_succeeded():
        print("\nDivide step failed!")
        return result_divide, result_combine
    print(f"Done divide! (took {end_divide_time - start_time})")

    ###########################################################################
    # Step two: combining the chunks per file (resolution 2) and preparing
    # metadata and overviews

    print("\nRunning combine step")

    @fused.udf(cache_max_age=0)
    def udf_combine(
        file_id: int,
        tmp_path: str,
        output_path: str,
        base_res: int = 7,
        chunk_res: int = 3,
    ):
        # define inline UDF that imports the helper function inside the UDF
        from job2.partition.tiff_to_h3 import udf_combine as run_udf_combine

        run_udf_combine(
            file_id,
            tmp_path,
            output_path,
            base_res=base_res,
            chunk_res=chunk_res,
        )

    # list available file_ids from the previous step
    orig = fused.options.request_timeout
    fused.options.request_timeout = 10
    file_ids = [path.strip("/").split("/")[-1] for path in fused.api.list(tmp_path)]
    fused.options.request_timeout = orig
    print(f"-- processing {len(file_ids)} file_ids")

    params = {
        "tmp_path": tmp_path,
        "output_path": output_path,
        #
        "base_res": base_res,
        "chunk_res": chunk_res,
    }
    submit_params = [{"file_id": i} for i in file_ids]

    result_combine = fused.submit(
        udf_combine,
        submit_params,
        **params,
        collect=False,
        **combine_kwargs,
        **kwargs,
    )
    result_combine.wait()
    end_combine_time = datetime.datetime.now()
    if not result_combine.all_succeeded():
        print("\nCombine step failed!")
        return result_divide, result_combine
    print(f"Done combine! (took {end_combine_time - end_divide_time})")

    ###########################################################################
    # Step 3: combining the metadata and overview tmp files

    print("\nRunning sample step")

    @fused.udf(cache_max_age=0)
    def udf_sample(output_path: str, remove_tmp_files: bool = True):
        from job2.partition.tiff_to_h3 import udf_sample as run_udf_sample

        run_udf_sample(
            output_path,
            remove_tmp_files=remove_tmp_files,
        )

    fused.run(udf_sample, output_path=output_path, remove_tmp_files=remove_tmp_files)
    print("Done sample!")

    print("\nRunning overview step")

    @fused.udf(cache_max_age=0)
    def udf_overview(output_path: str, res: int, remove_tmp_files: bool = True):
        from job2.partition.tiff_to_h3 import udf_overview as run_udf_overview

        run_udf_overview(
            output_path,
            res=res,
            remove_tmp_files=remove_tmp_files,
        )

    for res in [3, 4, 5, 6]:
        fused.run(
            udf_overview,
            output_path=output_path,
            res=res,
            remove_tmp_files=remove_tmp_files,
        )

    return result_divide, result_combine
