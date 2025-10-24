#!/usr/bin/env python3
"""Define the :class:`.Spark3D` object."""
import logging
import os
import shlex
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Literal

import numpy as np
import pandas as pd
from numpy.typing import NDArray

MODES = Literal[
    "Multipactor",
    "Video Multipactor",
    "Corona",
    "Video Corona",
    "--validate",
    "--list",
    "--config",
]
RF_UNITS_T = Literal["m", "mm", "inches"]
RF_UNITS = ("m", "mm", "inches")

FIELD_MAPS = (".dsp", ".f3e", ".mfe")


class Spark3D:
    """Spark3D simulation object."""

    _installation_folder = Path(os.environ.get("SPARK3DPATH", ""))
    _spark3d_bin = _installation_folder / "./spark3d"

    def __init__(
        self,
        project_path: Path,
        *files: str,
        output_path: Path | None = None,
        **kwargs,
    ) -> None:
        """Constructor.

        Parameters
        ----------
        project_path :
            Folder where the ``SPKX`` is stored.
        args :
            TODO
        output_path :
            Where results are stored. The default is None, which is changed to
            ``project_path`` during object construction.

        """
        if not self._installation_folder.is_dir():
            raise FileNotFoundError(
                "The `SPARK3DPATH` environment variable is unset or points to "
                "a non-existing folder.\n"
                f"$SPARK3DPATH={str(self._installation_folder)}"
            )
        if not self._spark3d_bin.is_file():
            raise FileNotFoundError(
                "The `spark3d` executable was not found in "
                f"{self._installation_folder}"
            )
        assert project_path.exists()
        self._project_path = project_path

        file_name, base_command = self._handle_different_input_types(
            *files, **kwargs
        )
        self._base_command = base_command

        self._output_path = (
            output_path
            if output_path is not None
            else self._project_path / Path(file_name).stem
        )

        self._results_path: Path | None = None
        # created by self._get_results_dir in self.run (path depends on the
        # configuration)

    def run(self, mode: MODES, config: dict[str, int] | None = None) -> None:
        """Launch the project.

        Parameters
        ----------
        mode :
            Type of simulation.
        config :
            Holds the information on the geometry, etc.

        """
        cmd = self._get_cmd(mode, config)
        if config is None:
            config = {}

        logging.info(
            "Running SPARK3D with command:\n"
            f"{' '.join(shlex.quote(c) for c in cmd)}"
        )
        try:
            with Popen(
                cmd,
                shell=False,
                env=os.environ,
                stdout=PIPE,
                stderr=PIPE,
                universal_newlines=True,
            ) as proc:
                assert proc.stdout is not None and proc.stderr is not None

                for line in proc.stdout:
                    logging.info(line.strip())

                proc.wait()

                stderr_output = proc.stderr.read().strip()
                if stderr_output:
                    logging.error("SPARK3D stderr:\n%s", stderr_output)

                logging.info(
                    "Run finished with return code %d.", proc.returncode
                )

                if proc.returncode != 0:
                    logging.error(
                        "This return code means that an error occurred during "
                        "SPARK3D execution."
                    )

        except OSError as err:
            logging.error("Failed to launch SPARK3D: %s", str(err))

    def get_full_results(
        self,
    ) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
        """Get the entire simulation results.

        .. todo::
            Auto-detection of results folder.

        Returns
        -------
        pd_power :
            Holds breakdown power, status (BD or noBD) and 'Multipactor order'.
        pd_time :
            Holds simulation number, power, and number of particles vs. time
            for every simulation (every power).

        """
        # TODO auto detect where the results are stored
        assert self._results_path is not None
        # old versions of SPARK3D
        # res_dir = self.results_path / "region1" / "signal1"
        res_dir = self._results_path / "region1" / "signalCW 1"
        assert res_dir.exists(), f"{res_dir} does not exist."

        res: list[pd.DataFrame | None]
        res = [None, None]
        for i, file in enumerate(["power_results.txt", "time_results.txt"]):
            file = res_dir / file
            if file.is_file():
                res[i] = pd.read_csv(file, delimiter="\t", na_values="---")

        pd_power, pd_time = res
        return pd_power, pd_time

    def get_results(self) -> tuple[NDArray, NDArray]:
        """Get a resume of results.

        Returns
        -------
        freq :
            Array of frequencies in Hz.
        power :
            Array of corresponding breakdown powers in W.

        """
        freq, power = None, None
        assert self._results_path is not None
        file = self._results_path / "general_results.txt"
        if file.is_file():
            freq, power = np.loadtxt(
                file, skiprows=1, delimiter="\t", usecols=(3, 4), unpack=True
            )
        if not isinstance(freq, np.ndarray):
            freq = np.array(freq)
        if not isinstance(power, np.ndarray):
            power = np.array(power)
        return freq, power

    def _handle_different_input_types(
        self,
        *args: str,
        new_project_name: Path | str | None = None,
        unitsRF: RF_UNITS_T | None = None,
    ) -> tuple[Path, list[str]]:
        """Handle the two types of input in a way that is transparent for user.

        .. todo::
            Check how HFSS files actually work

        Parameters
        ----------
        *args :
            Relative path to a ``SPKX`` OR relative path to a ``XML`` file and
            relative path to field map file (``DSP``, ``F3E`` or ``MFE``).
        new_project_name :
            Name of the project constructed from ``XML`` and field map file.
            ``SPKX`` extension must be provided. The default is None (then
            changed to 'my_project.spkx')
        unitsRF :
            Units of the file field map comes from HFSS (``DSP`` I think?).

        Raises
        ------
        IOError
            When the number of input file(s) and/or their type(s) are
            inconsistent.

        Returns
        -------
            The project name, the portion of command line that allows SPARK to
            identify or construct the project.

        """
        paths = [self._project_path / fp for fp in args]
        for path in paths:
            assert path.is_file(), f"Input file {path} does not exist."

        filetypes = [path.suffix for path in paths]

        if len(paths) == 1 and filetypes == [".spkx"]:
            cmd_input = f"--input={paths[0]}"
            return paths[0], [cmd_input]

        inter = [ext for ext in filetypes if ext in FIELD_MAPS]

        if new_project_name is None:
            new_project_name = "my_project.spkx"

        if len(paths) == 2 and ".xml" in filetypes and len(inter) == 1:
            i_field, i_xml = filetypes.index(inter[0]), filetypes.index(".xml")
            fp_field, fp_xml = paths[i_field], paths[i_xml]

            fp_project = self._project_path / new_project_name
            cmd_input = [f"--XMLfile={fp_xml}", f"--importRF={fp_field}"]

            if inter[0] == ".dsp":
                assert unitsRF in RF_UNITS, (
                    "The DSP is a HFSS field map file, right? In this case "
                    "you must provide a valid 'unitsRF' key."
                )
                cmd_input.append(f"unitsRF={unitsRF}")

            cmd_input.append(f"--projectName={fp_project}")

            return fp_project, cmd_input

        raise OSError(f"Inconsistent input files {args}")

    def _get_cmd(
        self, mode: MODES, config: dict[str, int] | None = None
    ) -> list[str]:
        """Create the command for the project.

        Parameters
        ----------
        mode :
            Type of simulation.
        config :
             Holds the information on the geometry, etc.

        Returns
        -------
            Command to launch simulation with appropriate arguments.

        """
        if config is None:
            config = {}

        cmd = [str(self._spark3d_bin)] + self._base_command

        spkx_kwargs = {
            "--output": self._output_path,
        }

        # No argument required, just validate the integrity of the file or list
        # the valid configurations
        if mode in ("--validate", "--list"):
            cmd.append(mode)
            return cmd

        if mode == "--config":
            logging.warning("Manually override mode, very patchy.")
            simulation_mode = "Multipactor"

            my_configuration = self._config_argument(simulation_mode, **config)
            self._results_path = self._output_path / self._get_results_dir(
                simulation_mode, **config
            )
            cmd.append(f"{mode}={my_configuration}")

            for key, value in spkx_kwargs.items():
                cmd.append(f"{key}={value}")
            return cmd

        raise OSError(f"configuration {mode} was not recognized.")

    def _config_argument(
        self,
        mode: MODES,
        project: int = 1,
        model: int = 1,
        confs: int = 1,
        em_conf: int = 1,
        discharge_conf: int = 1,
        video: int = 1,
    ) -> str:
        """Create the argument that goes after ``--config=``.

        Parameters
        ----------
        mode :
            Type of simulation to be performed.
        project :
            Project ID.
        model :
            Model ID.
        confs :
            Configurations ID.
        em_conf :
            EMConfigGroup ID.
        discharge_conf :
            MultipactorConfig or CoronaConfig ID.
        video :
            VideoMultipactorConfig or VideoCoronaConfig.

        Returns
        -------
        str
            Argument that goes after ``--config=``.

        """
        out = [
            f"Project:{project}",
            f"/Model:{model}",
            f"/Configurations:{confs}",
            f"/EMConfigGroup:{em_conf}",
        ]

        conf = {
            "Multipactor": f"/MultipactorConfig:{discharge_conf}//",
            "Video Multipactor": f"/MultipactorConfig:{discharge_conf}"
            + f"/VideoMultipactorConfig:{video}//",
            "Corona": f"/CoronaConfig:{discharge_conf}//",
            "Video Corona": f"/CoronaConfig:{discharge_conf}"
            + f"/VideoCoronaConfig:{video}//",
        }
        if mode not in conf:
            raise OSError("Invalid mode.")
        out.append(conf[mode])
        return "".join(out)

    # TODO: check dirs for Corona and Videos
    def _get_results_dir(
        self,
        mode: MODES,
        project: int = 1,
        model: int = 1,
        confs: int = 1,
        em_conf: int = 1,
        discharge_conf: int = 1,
        video: int = 1,
    ) -> Path:
        """Get the full path to the results folder.

        Parameters
        ----------
        mode :
            Type of simulation to be performed.
        project :
            Project ID.
        model :
            Model ID.
        confs :
            Configurations ID.
        em_conf :
            EMConfigGroup ID.
        discharge_conf :
            MultipactorConfig or CoronaConfig ID.
        video :
            VideoMultipactorConfig or VideoCoronaConfig.

        Returns
        -------
        pathlib.Path
            Path to the results.

        """
        out = [
            "Results",
            f"@Mod{model}",
            f"@ConfGr{confs}",
            f"@EMConfGr{em_conf}",
        ]

        d_mode = {
            "Multipactor": [f"@MuConf{discharge_conf}"],
            "Video Multipactor": [
                f"@MuConf{discharge_conf}",
                f"@Video{video}",
            ],
            "Corona": [f"@CoConf{discharge_conf}"],
            "Video Corona": [f"@CoConf{discharge_conf}", f"@Video{video}"],
        }
        out.extend(d_mode[mode])
        path = os.path.join(*out)
        return Path(path)


if __name__ == "__main__":
    import tempfile
    from importlib import resources

    output_path = Path(tempfile.mkdtemp())

    files = ("Coax_filter_CST(M, C, Eigenmode).spkx",)
    new_project_name = None

    # files = ("Coax_filter_CST(M, C, Eigenmode).xml", "Coax_filter_CST(M, C, Eigenmode).f3e")
    # new_project_name = output_path / "new_project.spkx"

    with resources.as_file(
        resources.files("spark3dbatch.data")
    ) as project_path:
        spk = Spark3D(
            project_path,
            *files,
            output_path=output_path,
            new_project_name=new_project_name,
        )

        mode = "--validate"
        config = {
            "project": 1,
            "model": 1,
            "confs": 1,
            "em_conf": 1,
            "discharge_conf": 1,
            "video": -1,
        }

        spk.run(mode, config)
        if mode == "--config":
            my_power, my_time = spk.get_full_results()
