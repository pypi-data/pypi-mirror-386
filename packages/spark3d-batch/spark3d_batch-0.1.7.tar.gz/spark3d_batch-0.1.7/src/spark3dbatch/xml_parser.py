#!/usr/bin/env python3
"""Define the class holding a SPARK3D configuration.

.. todo::
    Easily allow corona, videos.

"""
import logging
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from pathlib import Path

import numpy as np
from spark3dbatch.helper import fmt_array


class SparkXML:
    """A class to handle the ``XML`` files from SPARK3D."""

    #: Links ``d_conf`` keys with :class:`xml.etree.ElementTree.ElementTree`
    #: names
    _convert = {
        "Project": "project",
        "Model": "model",
        "Configurations": "confs",
        "EMConfigGroup": "em_conf",
        "MultipactorConfig": "discharge_conf",
    }

    def __init__(self, file: Path, keys: Sequence[str] | None = None) -> None:
        """Init object.

        Parameters
        ----------
        file :
            Path to the ``XML`` file.
        keys :
            Sequence of strings to indicate where the configuration should be
            in the ``XML`` file.

        """
        self.file = file
        self._tree = ET.parse(file)
        self._spark = self._tree.getroot()

        # Add a VideoMultipactorConfig key if needed, or change Multipactor to
        # corona
        self._keys = (
            tuple(keys)
            if keys is not None
            else (
                "Project",
                "Model",
                "Configurations",
                "EMConfigGroup",
                "MultipactorConfig",
            )
        )

    def get_config(self, **kwargs: int) -> ET.Element:
        """Return the configuration corresponding to the inputs.

        Parameters
        ----------
        *kwargs :
            Links configuration entries from ``self._keys`` to their value.

        Raises
        ------
        IOError
            ``*args`` matched no existing configuration. If it matched several,
            either the ``XML`` is wrong, either this code is wrong!

        Returns
        -------
        xml.etree.ElementTree.ElementTree
            Configuration.

        """
        keys_xml = (self._convert[key] for key in self._keys)
        values_xml = (kwargs[key] for key in keys_xml)

        path = (f"{key}[{val}]" for key, val in zip(self._keys, values_xml))
        configuration = self._spark.findall("/".join(path))
        if len(configuration) != 1:
            raise OSError("More than one or no configuration was found.")
        return configuration[0]

    def edit(
        self,
        conf: ET.Element,
        save: bool = False,
        **kwargs,
    ) -> None:
        """Modify the ``XML``.

        Parameters
        ----------
        conf :
            Configuration to be modified.
        save :
            To save the updated ``XML`` file. Previous file will be
            overwritten.
        **kwargs :
            Dict of values to change. Keys must be in ``<MultipactorConfig>``,
            eg ``'initialNumberElectrons'``. To modify inner keys, you must use
            the full path, eg ``'sweepPoints'`` will not work but
            ``'PowerSweep/sweepPoints'`` will. You must ensure that the type of
            the values matches what SPARK3D expects.

        """
        conf_key = conf.find("name")
        if conf_key is None:
            logging.error(
                f"Did not find a name for current {conf = }. Maybe it is "
                "malformed? Returning without attempting to edit it."
            )
            return

        logging.info(f"Modifying {conf_key.text}...")
        for key, new_value in kwargs.items():

            conf_val = conf.find(key)

            if conf_val is None:
                logging.warning(
                    f"Did not find a value for current {conf = }. Maybe it is "
                    "malformed? Skipping."
                )
                continue

            old_value = conf_val.text
            new_value = str(new_value)
            conf_val.text = new_value
            logging.info(f"Changed {key}: {old_value} to {new_value}")

        if save:
            self._tree.write(self.file)
            logging.info(f"XML saved in {self.file}")


if __name__ == "__main__":
    from importlib import resources

    file = (
        resources.files("spark3dbatch.data")
        / "Coax_filter_CST(M, C, Eigenmode).xml"
    )
    xml = SparkXML(file)

    # As already defined
    config = {
        "project": 1,
        "model": 1,
        "confs": 1,
        "em_conf": 1,
        "discharge_conf": 1,
        "video": -1,
    }
    xml_conf = xml.get_config(**config)

    power = fmt_array(np.linspace(1e-2, 1e2, 10))

    alter_conf = {
        "initialNumberElectrons": int(2e4),
        "pathRelativePrecision": 0.1,
        "PowerSweep/sweepPoints": power,
    }
    # Warning, save=True will overwrite previous ``XML``.
    xml.edit(xml_conf, save=False, **alter_conf)
