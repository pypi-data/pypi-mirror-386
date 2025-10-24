"""Handle OUTCAR."""

import re
import sys

import numpy as np

from parsevasp import utils
from parsevasp.base import BaseParser


class Outcar(BaseParser):
    """Class to handle OUTCAR."""

    ERROR_NO_ITERATIONS = 600
    BaseParser.ERROR_MESSAGES.update({ERROR_NO_ITERATIONS: 'A crash detected before the first SCF step.'})
    ERROR_MESSAGES = BaseParser.ERROR_MESSAGES

    def __init__(self, file_path=None, file_handler=None, logger=None):
        """Initialize an OUTCAR object and set content as a dictionary.

        Parameters
        ----------
        file_path : string
            A string containing the file path to the file that is going to be parsed.
        file_handler : object
            A file like object that acts as a handler for the content to be parsed.
        logger : object
            A logger object if you would like to use an external logger for messages
            ejected inside this parser.

        """

        super().__init__(file_path=file_path, file_handler=file_handler, logger=logger)

        # check that at least one is supplied
        if self._file_path is None and self._file_handler is None:
            self._logger.error(self.ERROR_MESSAGES[self.ERROR_USE_ONE_ARGUMENT])
            sys.exit(self.ERROR_USE_ONE_ARGUMENT)

        if self._file_path is None and self._file_handler is None:
            self._logger.error(self.ERROR_MESSAGES[self.ERROR_USE_ONE_ARGUMENT])
            sys.exit(self.ERROR_USE_ONE_ARGUMENT)

        self._data = {
            'elastic_moduli': {'non-symmetrized': None, 'symmetrized': None, 'total': None},
            'symmetry': {
                'num_space_group_operations': {'static': [], 'dynamic': []},
                'original_cell_type': {'static': [], 'dynamic': []},
                'symmetrized_cell_type': {'static': [], 'dynamic': []},
            },
            'magnetization': {
                'sphere': {
                    'x': {'site_moment': {}, 'total_magnetization': {}},
                    'y': {'site_moment': {}, 'total_magnetization': {}},
                    'z': {'site_moment': {}, 'total_magnetization': {}},
                },
                'full_cell': {},
            },
            'run_stats': {},
            'run_status': {
                'nelm': None,
                'nsw': None,
                'last_iteration_index': None,
                'finished': False,
                'ionic_converged': False,
                'electronic_converged': False,
                'consistent_nelm_breach': False,
                'contains_nelm_breach': False,
            },
        }

        # parse parse parse
        self._parse()

    def _write(self, *args, **kwargs):
        """Write not supported for OUTCAR."""
        raise NotImplementedError('Writing OUTCAR files is not supported.')

    def _parse(self):
        """Perform the actual parsing."""
        # Create dictionary from a file
        self._from_file()

    def _from_file(self):
        """
        Create a dictionary of entries from a
        file and store them in the this instance's data dictionary.
        """

        outcar = utils.read_from_file(self._file_path, self._file_handler, encoding='utf8')
        self._from_list(outcar)

    def _from_list(self, outcar):
        """
        Go through the list and extract what is not present in the XML file.

        Parameters
        ----------
        outcar : list
            A list of strings containing each line in the OUTCAR file.

        """
        config = ''
        s_orb = {0: 's', 1: 'p', 2: 'd', 3: 'f'}
        params = {'ibrion': -1}
        finished = False
        iter_counter = None
        nelec_steps = {}

        for index, line in enumerate(outcar):
            # Check the iteration counter
            match = re.search(r'Iteration *(\d+)\( *(\d+)\)', line)
            if match:
                iter_counter = [int(match.group(1)), int(match.group(2))]
                # Increment the counter
                if iter_counter[0] in nelec_steps:
                    nelec_steps[iter_counter[0]] += 1
                else:
                    nelec_steps[iter_counter[0]] = 1
                continue
            # Record the NELM / NSW requested
            utils.match_integer_param(self._data['run_status'], 'NSW', line)
            utils.match_integer_param(params, 'IBRION', line)
            utils.match_integer_param(self._data['run_status'], 'NELM', line)
            if 'NBANDS=' in line:
                self._data['run_status']['nbands'] = int(line.split('NBANDS=')[1].strip())
            # Test if the end of execution has reached
            if 'timing and accounting informations' in line:
                self._data['run_status']['finished'] = True
            # Fetch the symmetry
            if line.strip().startswith('Analysis of symmetry for initial positions (statically)'):
                config = 'static'
            if line.strip().startswith('Analysis of symmetry for dynamics'):
                config = 'dynamic'
            if config:
                if line.strip().startswith('Subroutine PRICEL returns'):
                    text = outcar[index + 1].strip().lower()
                    if text:
                        self._data['symmetry']['original_cell_type'][config].append('primitive cell')
                if 'primitive cells build up your supercell' in line:
                    text = f'{line.strip().split()} primitive cells'
                    self._data['symmetry']['original_cell_type'][config].append(text)
                if line.strip().startswith('Routine SETGRP: Setting up the symmetry group for a'):
                    self._data['symmetry']['symmetrized_cell_type'][config].append(outcar[index + 1].strip().lower())
                if line.strip().startswith('Subroutine GETGRP returns'):
                    self._data['symmetry']['num_space_group_operations'][config].append(int(line.strip().split()[4]))

            # then the elastic tensors etc. in kBar
            if line.strip().startswith('ELASTIC MODULI  (kBar)'):
                tensor = []
                for idx in range(3, 9):
                    tensor.append([float(item) for item in outcar[index + idx].strip().split()[1:]])
                self._data['elastic_moduli']['non_symmetrized'] = np.asarray(tensor)
            if line.strip().startswith('SYMMETRIZED ELASTIC MODULI'):
                tensor = []
                for idx in range(3, 9):
                    tensor.append([float(item) for item in outcar[index + idx].strip().split()[1:]])
                self._data['elastic_moduli']['symmetrized'] = np.asarray(tensor)
            if line.strip().startswith('TOTAL ELASTIC MODULI'):
                tensor = []
                for idx in range(3, 9):
                    tensor.append([float(item) for item in outcar[index + idx].strip().split()[1:]])
                self._data['elastic_moduli']['total'] = np.asarray(tensor)
            for _proj in ['x', 'y', 'z']:
                if line.strip().startswith(f'magnetization ({_proj})'):
                    _counter = 0
                    mag_found = False
                    while not mag_found:
                        if outcar[index + 4 + _counter].strip().split():
                            if not outcar[index + 4 + _counter].strip().startswith('-') and not outcar[
                                index + 4 + _counter
                            ].strip().startswith('tot'):
                                mag_line = outcar[index + 4 + _counter].split()
                                self._data['magnetization']['sphere'][f'{_proj}']['site_moment'][int(mag_line[0])] = {}
                                for _count, orb in enumerate(mag_line[1:-1]):
                                    self._data['magnetization']['sphere'][f'{_proj}']['site_moment'][int(mag_line[0])][
                                        s_orb[_count]
                                    ] = float(orb)
                                self._data['magnetization']['sphere'][f'{_proj}']['site_moment'][int(mag_line[0])][
                                    'tot'
                                ] = float(mag_line[-1])
                            if outcar[index + 4 + _counter].strip().startswith('tot'):
                                mag_line = outcar[index + 4 + _counter].split()
                                self._data['magnetization']['sphere'][f'{_proj}']['total_magnetization'] = {}
                                for _count, orb in enumerate(mag_line[1:-1]):
                                    self._data['magnetization']['sphere'][f'{_proj}']['total_magnetization'][
                                        s_orb[_count]
                                    ] = float(orb)
                                self._data['magnetization']['sphere'][f'{_proj}']['total_magnetization']['tot'] = float(
                                    mag_line[-1]
                                )
                                mag_found = True
                        else:
                            self._data['magnetization']['sphere'][f'{_proj}']['total_magnetization'] = {}
                            self._data['magnetization']['sphere'][f'{_proj}']['total_magnetization'] = self._data[
                                'magnetization'
                            ]['sphere'][f'{_proj}']['site_moment'][
                                next(iter(self._data['magnetization']['sphere'][f'{_proj}']['site_moment'].keys()))
                            ]
                            mag_found = True
                        _counter = _counter + 1
            if line.strip().startswith('number of electron'):
                # Only take the last value
                self._data['magnetization']['full_cell'] = [float(_val) for _val in line.strip().split()[5:]]

        # Check if SCF iterations are contained in the file
        if iter_counter is None:
            self._logger.error(self.ERROR_MESSAGES[self.ERROR_NO_ITERATIONS])
            sys.exit(self.ERROR_NO_ITERATIONS)

        # Work out if the ionic relaxation and electronic steps are to be considered converged
        run_status = self._data['run_status']
        run_status['last_iteration_index'] = iter_counter
        nsw = run_status['nsw']
        nelm = run_status['nelm']
        finished = run_status['finished']
        ibrion = params['ibrion']
        if finished is True:
            if ibrion > 0:
                # There are fewer number of ionic iterations than the set number of maximum number of
                # ionic iterations (NSW), thus the relaxation is considered converged.
                # Only relevant to check ionic relaxation convergence when IBRION is larger than zero
                if iter_counter[0] < nsw:
                    # Fewer iterations than requested - ionic relaxation is considered converged
                    # Note that this may include runs that has been interrupted
                    # by STOPCAR - this is a limitation of VASP
                    run_status['ionic_converged'] = True
                elif iter_counter[0] == nsw and nsw > 1:
                    # Reached the requested iterations - ionic relaxation is considered not converged
                    run_status['ionic_converged'] = False
                elif nsw <= 1:
                    # Sometimes we have no or only one ionic step, which makes it difficult to determine if the
                    # ionic relaxation is to be considered converged
                    self._logger.warning(
                        f'IBRION = {ibrion} but NSW is {nsw}'
                        ' - cannot deterimine if the relaxation structure is converged!'
                    )
                    run_status['ionic_converged'] = None
            else:
                # No ionic relaxation performed
                run_status['ionic_converged'] = None

            if iter_counter[1] < nelm:
                # There are fewer number of electronic steps in the last ionic iteration than the set maximum
                # number of electronic steps, thus the electronic self consistent cycle is considered converged
                run_status['electronic_converged'] = True

        # Check for consistent electronic convergence problems. VASP will not break when NELM is reached during
        # the relaxation, it will simply consider it converged. We need to detect this, which is done
        # by checking if there are any single run that have reached NELM in the history or if NELM
        # has been consistently reached.
        mask = [value >= nelm for sc_idx, value in sorted(nelec_steps.items(), key=lambda x: x[0])]
        if (finished and all(mask)) or (not finished and all(mask[:-1]) and iter_counter[0] > 1):
            # We have consistently reached NELM. Excluded the last iteration,
            # as the calculation may not be finished
            run_status['consistent_nelm_breach'] = True
        if any(mask):
            # We have at least one ionic step where NELM was reached.
            run_status['contains_nelm_breach'] = True

        self._data['run_stats'] = self._parse_timings_memory(outcar[-50:])

    def get_symmetry(self):
        """
        Return the symmetry.

        Parameters
        ----------
        None

        Returns
        -------
        symmetry : dict
            A dictionary containing the symmetry information.

        """

        symmetry = self._data['symmetry']
        return symmetry

    def get_elastic_moduli(self):
        """
        Return the elastic moduli in kBar.

        Parameters
        ----------
        None

        Returns
        -------
        elastic : dict
            A dictionary containing the elastic moduli.

        """

        elastic = self._data['elastic_moduli']
        return elastic

    def get_magnetization(self):
        """
        Return the magnetization of the cell.

        Parameters
        ----------
        None

        Returns
        -------
        magnetic : dict
            A dictionary containing the magnetization of the cell.

        """

        magnetic = self._data['magnetization']
        return magnetic

    def get_run_stats(self):
        """
        Return the run time statistics information.

        The existence of timing and memory information also signals the calculation terminate
        gracefully.

        Parameters
        ----------
        None

        Returns
        -------
        stats : dict
            A dictionary containing timing and memory consumption information
            that are parsed from the end of the OUTCAR file. The key names are
            mostly preserved, except for the memory which is prefixed with `mem_usage_`.
            Units are preserved from OUTCAR and there are some differences between
            VASP 5 and 6.

        """

        stats = self._data['run_stats']
        return stats

    def get_run_status(self):
        """
        Return the status of the run.

        Contains information of the convergence of the ionic relaxation and electronics,
        in addition to information if the run has finished.

        Parameters
        ----------
        None

        Returns
        -------
        status : dict
            A dictionary containing the keys `finished`, which is True if the VASP calculation
            contain timing information in the end of the OUTCAR. The key `ionic_converged` is
            True if the number of ionic steps detected is smaller than the supplied NSW.
            The key `electronic_converged` is True if the number of electronic steps is smaller than
            NELM (defaults to 60 in VASP). It is also possible to check if all the ionic steps
            did reached NELM and thus did not converged if the key `consistent_nelm_breach` is True,
            while `contains_nelm_breach` is True if one or more ionic steps reached NELM and thus
            did not converge electronically.

        """

        status = self._data['run_status']
        return status

    @staticmethod
    def _parse_timings_memory(timing_lines):
        """
        Parse timing information.

        Parameters
        ----------
        timing_lines : list
            A list of lines containing the timing information.

        Returns
        -------
        info : dict
            A dictionary containing the timing information.
        """
        info = {}
        time_mem_pattern = re.compile(r'\((sec|kb)\)')
        mem_pattern = re.compile(r':.*kBytes$')
        for _, line in enumerate(timing_lines):
            if time_mem_pattern.search(line):
                tokens = line.strip().split(':')
                item_name = '_'.join(tmp.lower() for tmp in tokens[0].strip().split()[:-1])
                # The entry can be empty (VASP6)
                try:
                    info[item_name] = float(tokens[1].strip())
                except ValueError:
                    info[item_name] = None

            elif mem_pattern.search(line):
                tokens = re.split(r'[: ]+', line.strip())
                try:
                    info['mem_usage_' + tokens[0]] = float(tokens[-2])
                except ValueError:
                    info['mem_usage_' + tokens[0]] = None

        return info
