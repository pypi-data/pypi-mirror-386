import asyncio
import concurrent.futures
import functools
import glob
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union

from .exceptions import LayerNotFoundInModel
from .utils import download

METADATA_FILENAME = ".metadata.json"

FILE_EXT = [
    "gpml",
    "gpmlz",
    "gpml.gz",
    "dat",
    "pla",
    "shp",
    "geojson",
    "json",
    ".gpkg",
    "gmt",
    "vgp",
]

logger = logging.getLogger("pmm")


class PlateModel:
    """Download and manage files required for a plate reconstruction model.

    👀👇 **LOOK HERE!!!** 👀👇

    Normally you should always use :py:meth:`PlateModelManager.get_model()` to get a :class:`PlateModel` object.
    Create a :class:`PlateModel` object directly only when you don't have Internet connection and would like
    to use the local model files in ``readonly`` mode.
    Do not create a :class:`PlateModel` object directly if you have no idea what's going on.

    .. seealso::

        `Use PlateModel class in readonly mode. <examples.html#use-without-internet>`__
    """

    def __init__(
        self,
        model_name: str,
        model_cfg=None,
        data_dir: str = ".",
        readonly=False,
        timeout=(None, None),
    ):
        """Constructor. Create a :class:`PlateModel` instance.

        :param model_name: The model name of interest.
        :type model_name: str
        :param model_cfg: The model configuration in JSON format.
                          The configuration is either downloaded from the server or
                          loaded from a local file ``.metadata.json``. If you are confused by this parameter,
                          use :py:meth:`PlateModelManager.get_model()` to get a :class:`PlateModel` object instead.
        :param data_dir: The folder path to save the model data.
        :type data_dir: str, default="."
        :param readonly: If this flag is set to ``True``, The :class:`PlateModel` object will use
                         the files in the local folder and will not attempt to
                         download/update the files from the server.
        :type readonly: bool, default=False
        :param timeout: Network connection `timeout parameter <https://requests.readthedocs.io/en/latest/user/advanced/#timeouts>`__.
        """
        self.model_name = model_name.lower()
        self.meta_filename = METADATA_FILENAME
        self._model = model_cfg
        self.readonly = readonly
        self.timeout = timeout

        self.data_dir = data_dir

        self.model_dir = f"{self.data_dir}/{self.model_name}"

        if readonly:
            if not PlateModel.is_model_dir(self.model_dir):
                raise Exception(
                    f"{self.model_dir} must be valid model dir in readonly mode."
                )
            else:
                with open(f"{self.model_dir}/{self.meta_filename}", "r") as f:
                    self._model = json.load(f)

        if not readonly:
            # async and concurrent things
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=15)
            self.loop = asyncio.new_event_loop()
            self.run = functools.partial(self.loop.run_in_executor, self.executor)
            asyncio.set_event_loop(self.loop)

        if self._model is None:
            logger.warning(
                "Creating a PlateModel instance with the 'model configuration' is None. Normally this should not happen. I allow this just in case some genius is doing something extraordinarily smart."
            )

    @property
    def model(self) -> Dict:
        """The model metadata."""
        if self._model is not None:
            return self._model
        else:
            raise Exception(
                "The 'model configuration' is None. This should not happen. Something extraordinary must have happened. Think carefully what you have done!!!"
            )

    @model.setter
    def model(self, var) -> None:
        if var is None:
            logger.warning(
                "You are trying to set the 'model configuration' to None. I will allow this. But I hope you know what you are doing!!!"
            )
        self._model = var

    def __getstate__(self):
        attributes = self.__dict__.copy()
        del attributes["executor"]
        del attributes["loop"]
        del attributes["run"]
        return attributes

    def __setstate__(self, state):
        self.__dict__ = state
        if not self.readonly:
            # async and concurrent things
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=15)
            self.loop = asyncio.new_event_loop()
            self.run = functools.partial(self.loop.run_in_executor, self.executor)
            asyncio.set_event_loop(self.loop)

    def __del__(self):
        if not self.readonly:
            try:
                self.loop.close()
            except:
                pass  # ignore the exception when closing the loop if any

    def get_cfg(self):
        """Return the model configuration."""
        return self.model

    def get_model_dir(self):
        """Return the path to a folder containing the model files."""
        if PlateModel.is_model_dir(self.model_dir):
            return self.model_dir
        elif not self.readonly:
            return self.create_model_dir()
        else:
            raise Exception(
                f"The model dir {self.model_dir} is invalid and could not create it (in readonly mode)."
            )

    def get_data_dir(self):
        """Return the path to a folder (parent folder of the ``model dir``) containing a set of downloaded models."""
        return self.data_dir

    def set_data_dir(self, new_dir):
        """Change the folder (parent folder of the ``model dir``) in which you would like to save your model."""
        self.data_dir = new_dir
        self.model_dir = f"{self.data_dir}/{self.model_name}/"

    def get_big_time(self):
        """The max (big number in Ma) reconstruction time in the model."""
        return self.model["BigTime"]

    def get_small_time(self):
        """The min (small number in Ma) reconstruction time in the model."""
        return self.model["SmallTime"]

    def get_avail_layers(self):
        """Get all available layers in this plate model."""
        if not self.model:
            raise Exception("Fatal: No model configuration found!")
        return list(self.model["Layers"].keys())

    def get_rotation_model(self):
        """Return a list of rotation files."""
        if not self.readonly:
            rotation_folder = self._download_layer_files("Rotations")
        else:
            rotation_folder = f"{self.model_dir}/Rotations"
        rotation_files = glob.glob(f"{rotation_folder}/*.rot")
        rotation_files.extend(glob.glob(f"{rotation_folder}/*.grot"))
        # print(rotation_files)
        return rotation_files

    def get_coastlines(
        self, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Return a list of ``coastlines`` files."""
        return self.get_layer(
            "Coastlines", return_none_if_not_exist=return_none_if_not_exist
        )

    def get_static_polygons(
        self, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Return a list of ``static polygons`` files."""
        return self.get_layer(
            "StaticPolygons", return_none_if_not_exist=return_none_if_not_exist
        )

    def get_continental_polygons(
        self, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Return a list of ``continental polygons`` files."""
        return self.get_layer(
            "ContinentalPolygons", return_none_if_not_exist=return_none_if_not_exist
        )

    def get_topologies(
        self, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Return a list of ``topologies`` files."""
        return self.get_layer(
            "Topologies", return_none_if_not_exist=return_none_if_not_exist
        )

    def get_COBs(
        self, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Return a list of ``Continent-Ocean Boundaries`` files."""
        return self.get_layer("COBs", return_none_if_not_exist=return_none_if_not_exist)

    def get_layer(
        self, layer_name: str, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Get a list of layer files by a layer name. Call :meth:`get_avail_layers` to get all the available layer names.

        Raise :class:`LayerNotFoundInModel` exception to get user's attention by default.
        Set ``return_none_if_not_exist`` to ``True`` if you don't want to see the :class:`LayerNotFoundInModel` exception.

        :param layer_name: The layer name of interest.
        :param return_none_if_not_exist: If set to ``True``, return ``None`` when the layer does not exist in the model.

        :returns: A list of file names or ``None`` if ``return_none_if_not_exist`` is set to ``True``.

        :raises :class:`LayerNotFoundInModel`: Raise this exception if the layer name does not exist in this model.

        """
        try:
            if not self.readonly:
                layer_folder = self._download_layer_files(layer_name)
            else:
                layer_folder = f"{self.model_dir}/{layer_name}"
            files = []
            for ext in FILE_EXT:
                files.extend(glob.glob(f"{layer_folder}/*.{ext}"))

            return files
        except LayerNotFoundInModel as e:
            logger.warning(e)
            if return_none_if_not_exist:
                logger.warning(
                    f"The layer({layer_name}) does not exist in model({self.model_name})."
                )
                return None
            else:
                raise e

    def get_raster(self, raster_name: str, time: Union[int, float]) -> str:
        """Return a local path for the raster file.

        :param time: A single time of interest.
        :type time: int or float

        :returns: A local path of the raster file.
        :rtype: str
        """

        if not "TimeDepRasters" in self.model:
            raise Exception("No time-dependent rasters found in this model.")
        if not raster_name in self.model["TimeDepRasters"]:
            raise Exception(
                f"Time-dependent rasters ({raster_name}) not found in this model. {self.model['TimeDepRasters']}"
            )
        url = self.model["TimeDepRasters"][raster_name].format(time)

        if not self.readonly:
            self._download_raster(url, f"{self.get_model_dir()}/Rasters/{raster_name}")
        file_name = url.split("/")[-1]
        local_path = f"{self.get_model_dir()}/Rasters/{raster_name}/{file_name}"
        if os.path.isfile(local_path):
            return local_path
        elif self.readonly:
            raise Exception(
                f"You are in readonly mode and the raster {url} has not been downloaded yet."
            )
        else:
            raise Exception(f"Failed to download {url}")

    def get_rasters(
        self, raster_name: str, times: List[Union[int, float]]
    ) -> List[str]:
        """Return local paths for the raster files.

        :param times: A list of times
        :returns: A list of local paths
        """
        if not "TimeDepRasters" in self.model:
            raise Exception("No time-dependent rasters found in this model.")
        if not raster_name in self.model["TimeDepRasters"]:
            raise Exception(
                f"Time-dependent rasters ({raster_name}) not found in this model. {self.model['TimeDepRasters']}"
            )

        if not self.readonly:
            self.download_time_dependent_rasters(raster_name, times)

        paths = []
        for time in times:
            url = self.model["TimeDepRasters"][raster_name].format(time)
            file_name = url.split("/")[-1]
            local_path = f"{self.get_model_dir()}/Rasters/{raster_name}/{file_name}"
            if os.path.isfile(local_path):
                paths.append(local_path)
            elif self.readonly:
                raise Exception(
                    f"You are in readonly mode and the raster {url} has not been downloaded yet."
                )
            else:
                raise Exception(f"Failed to download {url}")
        return paths

    def create_model_dir(self):
        """Create a folder with a file ``.metadata.json`` in it to keep the model files."""
        if self.readonly:
            raise Exception("Unable to create model dir in readonly mode.")
        if not self.model_dir:
            raise Exception(f"Error: model dir is {self.model_dir}")

        # model dir already exists
        if PlateModel.is_model_dir(self.model_dir):
            return self.model_dir

        model_path = self.model_dir
        if os.path.isfile(model_path):
            raise Exception(
                f"Fatal: the model folder {model_path} already exists and is a file!! Remove the file or use another path."
            )

        Path(model_path).mkdir(parents=True, exist_ok=True)

        metadata_file = f"{model_path}/{self.meta_filename}"
        if not os.path.isfile(metadata_file):
            with open(metadata_file, "w+") as f:
                json.dump(self.model, f)

        return model_path

    @staticmethod
    def is_model_dir(folder_path: str):
        """Return ``True`` if the folder contains files of a plate model, otherwise ``False``."""
        return os.path.isdir(folder_path) and os.path.isfile(
            f"{folder_path}/.metadata.json"
        )

    def purge(self):
        """Remove the model folder and everything inside the folder."""
        if os.path.isdir(self.model_dir):
            shutil.rmtree(self.model_dir)

    def purge_layer(self, layer_name):
        """Remove the layer folder of the given layer name."""
        layer_path = f"{self.model_dir}/{layer_name}"
        if os.path.isdir(layer_path):
            shutil.rmtree(layer_path)

    def purge_time_dependent_rasters(self, raster_name):
        """Remove the raster folder of the given raster name."""
        raster_path = f"{self.model_dir}/{raster_name}"
        if os.path.isdir(raster_path):
            shutil.rmtree(raster_path)

    def _download_layer_files(self, layer_name):
        """Download layer files for a given layer name. You should use :meth:`get_layer`, instead of this one, whenever possible.

        The layer files are in a ".zip" file. This function will download and unzip it.

        :param layer_name: the layer name, such as "Rotations","Coastlines", "StaticPolygons", "ContinentalPolygons", "Topologies", etc.
                           Call :meth:`get_avail_layers` to get all the available layer names.

        :returns: the folder path which contains the layer files

        """
        if self.readonly:
            raise Exception("Unable to download layer files in readonly mode.")

        layer_file_url = self._get_layer_file_url(layer_name)

        model_folder = self.create_model_dir()
        layer_folder = f"{model_folder}/{layer_name}"
        metadata_file = f"{layer_folder}/{self.meta_filename}"

        downloader = download.FileDownloader(
            layer_file_url, metadata_file, model_folder, timeout=self.timeout
        )
        # only re-download when necessary
        if downloader.check_if_file_need_update():
            if os.path.isdir(layer_folder):
                # move the old layer files into "history" folder
                timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                history_dir = f"{model_folder}/history/{layer_name}_{timestamp_str}"
                Path(history_dir).mkdir(parents=True, exist_ok=True)
                shutil.move(layer_folder, history_dir)

            downloader.download_file_and_update_metadata()
        else:
            if downloader.check_if_expire_date_need_update():
                # update the expiry date
                downloader.update_metadata()

            logger.debug(
                f"The local files in {layer_folder} are still good. Will not download again at this moment."
            )

        return layer_folder

    def download_all_layers(self):
        """Download all layers. This function calls :meth:`download_layer_files()` on every available layer."""
        if self.readonly:
            raise Exception("Unable to download all layers in readonly mode.")

        async def f():
            tasks = []
            if "Rotations" in self.model:
                tasks.append(self.run(self._download_layer_files, "Rotations"))
            if "Layers" in self.model:
                for layer in self.model["Layers"]:
                    tasks.append(self.run(self._download_layer_files, layer))

            # print(tasks)
            await asyncio.wait(tasks)

        try:
            self.loop.run_until_complete(f())
        except RuntimeError:
            import nest_asyncio

            nest_asyncio.apply()
            self.loop.run_until_complete(f())

    def get_avail_time_dependent_raster_names(self):
        """Return all time-dependent raster names in this plate model."""
        if not "TimeDepRasters" in self.model:
            return []
        else:
            return [name for name in self.model["TimeDepRasters"]]

    def download_time_dependent_rasters(self, raster_name, times=None):
        """Download time-dependent rasters for a given raster name.

        Call :meth:`get_avail_time_dependent_raster_names()` to see all the available raster names in this model.

        :param raster_name: the raster name of interest
        :param times: if not given, download from begin to end with 1My interval
        """
        if self.readonly:
            raise Exception(
                "Unable to download time dependent rasters in readonly mode."
            )

        if (
            "TimeDepRasters" in self.model
            and raster_name in self.model["TimeDepRasters"]
        ):

            async def f():
                nonlocal times
                tasks = []

                dst_path = f"{self.get_model_dir()}/Rasters/{raster_name}"
                if not times:
                    times = range(self.model["SmallTime"], self.model["BigTime"] + 1)
                for time in times:
                    tasks.append(
                        self.run(
                            self._download_raster,
                            self.model["TimeDepRasters"][raster_name].format(time),
                            dst_path,
                        )
                    )

                # print(tasks)
                await asyncio.wait(tasks)

            try:
                self.loop.run_until_complete(f())
            except RuntimeError:
                import nest_asyncio

                nest_asyncio.apply()
                self.loop.run_until_complete(f())

        else:
            raise Exception(
                f"Unable to find {raster_name} configuration in this model {self.model_name}."
            )

    def _download_raster(self, url, dst_path):
        """Download a single raster file from ``url`` and save the file in ``dst_path``.

        A metadata file will also be created for the raster file in folder ``f"{dst_path}/metadata"``

        :param url: the url to the raster file
        :param dst_path: the folder path to save the raster file

        """
        if self.readonly:
            raise Exception("Unable to download raster in readonly mode.")
        filename = url.split("/")[-1]
        metadata_folder = f"{dst_path}/.metadata"
        metadata_file = f"{metadata_folder}/{filename}.json"

        downloader = download.FileDownloader(
            url, metadata_file, dst_path, timeout=self.timeout
        )
        # only re-download when necessary
        if downloader.check_if_file_need_update():
            downloader.download_file_and_update_metadata()
        else:
            if downloader.check_if_expire_date_need_update():
                # update the expiry date
                downloader.update_metadata()

            logger.debug(
                f"The local raster file {dst_path}/{filename} is still good. Will not download again at this moment."
            )

    def download_all(self):
        """Download everything in this plate model."""
        if self.readonly:
            raise Exception("Unable to download all in readonly mode.")
        self.download_all_layers()
        if "TimeDepRasters" in self.model:
            for raster in self.model["TimeDepRasters"]:
                self.download_time_dependent_rasters(raster)

    def _get_layer_file_url(self, layer_name: str):
        # find the layer file url. two parts. one is the rotation, the other is all other geometry layers
        if layer_name == "Rotations":
            # for Rotations
            return self.model[layer_name]
        elif "Layers" in self.model and layer_name in self.model["Layers"]:
            # for other geometry layers
            return self.model["Layers"][layer_name]
        else:
            logger.debug(f"{json.dumps(self.model, indent=4)}")
            raise LayerNotFoundInModel(
                f"The layer({layer_name}) was not found in model({self.model_name})."
            )
