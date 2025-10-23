from AOT_biomaps.AOT_Recon.AlgebraicRecon import AlgebraicRecon
from AOT_biomaps.AOT_Recon.ReconEnums import ReconType, OptimizerType, PotentialType, ProcessType
from .ReconTools import check_gpu_memory, calculate_memory_requirement
from .AOT_Optimizers import MAPEM, DEPIERRO
from AOT_biomaps.Config import config

import warnings
import numpy as np
import os
from datetime import datetime

class BayesianRecon(AlgebraicRecon):
    """
    This class implements the Bayesian reconstruction process.
    It currently does not perform any operations but serves as a template for future implementations.
    """
    def __init__(self, 
                opti = OptimizerType.PGC,
                potentialFunction = PotentialType.HUBER_PIECEWISE,  
                beta=None, 
                delta=None, 
                gamma=None, 
                sigma=None,
                corner = (0.5-np.sqrt(2)/4)/np.sqrt(2),
                face = 0.5-np.sqrt(2)/4, 
                **kwargs):
        super().__init__(**kwargs)
        self.reconType = ReconType.Bayesian
        self.potentialFunction = potentialFunction
        self.optimizer = opti
        self.beta = beta           
        self.delta = delta          # typical value is 0.1
        self.gamma = gamma          # typical value is 0.01
        self.sigma = sigma          # typical value is 1.0
        self.corner = corner        # typical value is (0.5-np.sqrt(2)/4)/np.sqrt(2)
        self.face = face            # typical value is 0.5-np.sqrt(2)/4 

        if not isinstance(self.potentialFunction, PotentialType):
            raise TypeError(f"Potential functions must be of type PotentialType, got {type(self.potentialFunction)}")  

    def checkExistingFile(self, date = None):
        """
        Check if the reconstruction file already exists, based on current instance parameters.

        Args:
            withTumor (bool): If True, checks the phantom file; otherwise, checks the laser file.
            overwrite (bool): If False, returns False if the file exists.

        Returns:
            tuple: (bool: whether to save, str: the filepath)
        """
        if self.saveDir is None:
            raise ValueError("Save directory is not specified.")

        # Construction du chemin du fichier
        if date is None:
            date = datetime.now().strftime("%d%m")

        opt_name = self.optimizer.value
        pot_name = self.potentialFunction.value
        dir_name = f'results_{date}_{opt_name}_{pot_name}'

        if self.optimizer == OptimizerType.PPGMLEM:
            dir_name += f'_Beta_{self.beta}_Delta_{self.delta}_Gamma_{self.gamma}_Sigma_{self.sigma}'
        elif self.optimizer in (OptimizerType.PGC, OptimizerType.DEPIERRO95):
            dir_name += f'_Beta_{self.beta}_Sigma_{self.sigma}'

        results_dir = os.path.join(self.saveDir, dir_name)

        if os.path.exists(os.path.join(results_dir,"reconIndices.npy")):
            return (True, results_dir)

        return (False, results_dir)

    def load(self, withTumor=True, results_date=None, optimizer=None, potential_function=None, filePath=None):
        """
        Load the reconstruction results and indices as lists of 2D np arrays for Bayesian reconstruction and store them in self.
        If the loaded file is a 3D array, it is split into a list of 2D arrays.
        """
        if filePath is not None:
            # Mode chargement direct depuis un fichier
            recon_key = 'reconPhantom' if withTumor else 'reconLaser'
            recon_path = filePath
            if not os.path.exists(recon_path):
                raise FileNotFoundError(f"No reconstruction file found at {recon_path}.")
            # Charge le fichier (3D ou liste de 2D)
            data = np.load(recon_path, allow_pickle=True)
            # Découpe en liste de 2D si c'est un tableau 3D
            if isinstance(data, np.ndarray) and data.ndim == 3:
                if withTumor:
                    self.reconPhantom = [data[i, :, :] for i in range(data.shape[0])]
                else:
                    self.reconLaser = [data[i, :, :] for i in range(data.shape[0])]
            else:
                # Sinon, suppose que c'est déjà une liste de 2D
                if withTumor:
                    self.reconPhantom = data
                else:
                    self.reconLaser = data
            # Essayer de charger les indices
            base_dir, file_name = os.path.split(recon_path)
            indices_path = os.path.join(base_dir, 'indices.npy')
            if os.path.exists(indices_path):
                indices_data = np.load(indices_path, allow_pickle=True)
                if isinstance(indices_data, np.ndarray) and indices_data.ndim == 3:
                    self.indices = [indices_data[i, :, :] for i in range(indices_data.shape[0])]
                else:
                    self.indices = indices_data
            else:
                self.indices = None
            print(f"Loaded reconstruction results and indices from {recon_path}")
        else:
            # Mode chargement depuis le répertoire de résultats
            if self.saveDir is None:
                raise ValueError("Save directory is not specified. Please set saveDir before loading.")
            # Use current optimizer and potential function if not provided
            opt_name = optimizer.value if optimizer is not None else self.optimizer.value
            pot_name = potential_function.value if potential_function is not None else self.potentialFunction.value
            # Build the base directory pattern
            dir_pattern = f'results_*_{opt_name}_{pot_name}'
            # Add parameters to the pattern based on the optimizer
            if optimizer is None:
                optimizer = self.optimizer
            if optimizer == OptimizerType.PPGMLEM:
                beta_str = f'_Beta_{self.beta}'
                delta_str = f'_Delta_{self.delta}'
                gamma_str = f'_Gamma_{self.gamma}'
                sigma_str = f'_Sigma_{self.sigma}'
                dir_pattern += f'{beta_str}{delta_str}{gamma_str}{sigma_str}'
            elif optimizer in (OptimizerType.PGC, OptimizerType.DEPIERRO95):
                beta_str = f'_Beta_{self.beta}'
                sigma_str = f'_Sigma_{self.sigma}'
                dir_pattern += f'{beta_str}{sigma_str}'
            # Find the most recent results directory if no date is specified
            if results_date is None:
                dirs = [d for d in os.listdir(self.saveDir) if os.path.isdir(os.path.join(self.saveDir, d)) and dir_pattern in d]
                if not dirs:
                    raise FileNotFoundError(f"No matching results directory found for pattern '{dir_pattern}' in {self.saveDir}.")
                dirs.sort(reverse=True)  # Most recent first
                results_dir = os.path.join(self.saveDir, dirs[0])
            else:
                results_dir = os.path.join(self.saveDir, f'results_{results_date}_{opt_name}_{pot_name}')
                if optimizer == OptimizerType.PPGMLEM:
                    results_dir += f'_Beta_{self.beta}_Delta_{self.delta}_Gamma_{self.gamma}_Sigma_{self.sigma}'
                elif optimizer in (OptimizerType.PGC, OptimizerType.DEPIERRO95):
                    results_dir += f'_Beta_{self.beta}_Sigma_{self.sigma}'
                if not os.path.exists(results_dir):
                    raise FileNotFoundError(f"Directory {results_dir} does not exist.")
            # Load reconstruction results
            recon_key = 'reconPhantom' if withTumor else 'reconLaser'
            recon_path = os.path.join(results_dir, f'{recon_key}.npy')
            if not os.path.exists(recon_path):
                raise FileNotFoundError(f"No reconstruction file found at {recon_path}.")
            data = np.load(recon_path, allow_pickle=True)
            if isinstance(data, np.ndarray) and data.ndim == 3:
                if withTumor:
                    self.reconPhantom = [data[i, :, :] for i in range(data.shape[0])]
                else:
                    self.reconLaser = [data[i, :, :] for i in range(data.shape[0])]
            else:
                if withTumor:
                    self.reconPhantom = data
                else:
                    self.reconLaser = data
            # Load saved indices as list of 2D arrays
            indices_path = os.path.join(results_dir, 'indices.npy')
            if not os.path.exists(indices_path):
                raise FileNotFoundError(f"No indices file found at {indices_path}.")
            indices_data = np.load(indices_path, allow_pickle=True)
            if isinstance(indices_data, np.ndarray) and indices_data.ndim == 3:
                self.indices = [indices_data[i, :, :] for i in range(indices_data.shape[0])]
            else:
                self.indices = indices_data
            print(f"Loaded reconstruction results and indices from {results_dir}")

    def run(self, processType=ProcessType.PYTHON, withTumor=True):
        """
        This method is a placeholder for the Bayesian reconstruction process.
        It currently does not perform any operations but serves as a template for future implementations.
        """
        if(processType == ProcessType.CASToR):
            self._bayesianReconCASToR(withTumor)
        elif(processType == ProcessType.PYTHON):
            self._bayesianReconPython(withTumor)
        else:
            raise ValueError(f"Unknown Bayesian reconstruction type: {processType}")
        
    def _bayesianReconCASToR(self, withTumor):
        raise NotImplementedError("CASToR Bayesian reconstruction is not implemented yet.")

    def _bayesianReconPython(self, withTumor):

        if withTumor:
            if self.experiment.AOsignal_withTumor is None:
                raise ValueError("AO signal with tumor is not available. Please generate AO signal with tumor the experiment first in the experiment object.")
            if self.optimizer.value ==  OptimizerType.PPGMLEM.value:
                self.reconPhantom, self.indices = self._MAPEM_STOP(SMatrix=self.SMatrix, y=self.experiment.AOsignal_withTumor, withTumor=withTumor)
            elif self.optimizer.value == OptimizerType.PGC.value:
                self.reconPhantom, self.indices = self._MAPEM(SMatrix=self.SMatrix, y=self.experiment.AOsignal_withTumor, withTumor=withTumor)
            elif self.optimizer.value == OptimizerType.DEPIERRO95.value:
                self.reconPhantom, self.indices = self._DEPIERRO(SMatrix=self.SMatrix, y=self.experiment.AOsignal_withTumor, withTumor=withTumor)
            else:
                raise ValueError(f"Unknown optimizer type: {self.optimizer.value}")
        else:
            if self.experiment.AOsignal_withoutTumor is None:
                raise ValueError("AO signal without tumor is not available. Please generate AO signal without tumor the experiment first in the experiment object.")
            if self.optimizer.value ==  OptimizerType.PPGMLEM.value:
                self.reconLaser, self.indices = self._MAPEM_STOP(SMatrix=self.SMatrix, y=self.experiment.AOsignal_withoutTumor, withTumor=withTumor)
            elif self.optimizer.value == OptimizerType.PGC.value:
                self.reconLaser, self.indices = self._MAPEM(SMatrix=self.SMatrix, y=self.experiment.AOsignal_withoutTumor, withTumor=withTumor)
            elif self.optimizer.value == OptimizerType.DEPIERRO95.value:
                self.reconLaser, self.indices = self._DEPIERRO(SMatrix=self.SMatrix, y=self.experiment.AOsignal_withoutTumor, withTumor=withTumor)
            else:
                raise ValueError(f"Unknown optimizer type: {self.optimizer.value}")

    def _MAPEM_STOP(self, SMatrix, y, withTumor):
        """
        This method implements the MAPEM_STOP algorithm using either CPU or single-GPU PyTorch acceleration.
        Multi-GPU and Multi-CPU modes are not implemented for this algorithm.
        """
        result = None
        required_memory = calculate_memory_requirement(SMatrix, y)

        if self.isGPU:
            if check_gpu_memory(config.select_best_gpu(), required_memory):
                try:
                    result = MAPEM._MAPEM_GPU_STOP(SMatrix=SMatrix, y=y, Omega=self.potentialFunction, numIterations=self.numIterations, beta=self.beta, delta=self.delta, gamma=self.gamma, sigma=self.sigma, isSavingEachIteration=self.isSavingEachIteration, withTumor=withTumor)
                except Exception as e:
                    warnings.warn(f"Falling back to CPU implementation due to an error in GPU implementation: {e}")
            else:
                warnings.warn("Insufficient GPU memory for single GPU MAPEM_STOP. Falling back to CPU.")

        if result is None:
            try:
                result = MAPEM._MAPEM_CPU_STOP(SMatrix=SMatrix, y=y, Omega=self.potentialFunction, numIterations=self.numIterations, beta=self.beta, delta=self.delta, gamma=self.gamma, sigma=self.sigma, isSavingEachIteration=self.isSavingEachIteration, withTumor=withTumor)
            except Exception as e:
                warnings.warn(f"An error occurred in CPU implementation: {e}")
                result = None

        return result

    def _MAPEM(self, SMatrix, y, withTumor):
        """
        This method implements the MAPEM algorithm using either CPU or single-GPU PyTorch acceleration.
        Multi-GPU and Multi-CPU modes are not implemented for this algorithm.
        """
        result = None
        required_memory = calculate_memory_requirement(SMatrix, y)

        if self.isGPU:
            if check_gpu_memory(config.select_best_gpu(), required_memory):
                try:
                    result = MAPEM._MAPEM_GPU(SMatrix=SMatrix, y=y, Omega=self.potentialFunction, numIterations=self.numIterations, beta=self.beta, delta=self.delta, gamma=self.gamma, sigma=self.sigma, isSavingEachIteration=self.isSavingEachIteration, withTumor=withTumor)
                except Exception as e:
                    warnings.warn(f"Falling back to CPU implementation due to an error in GPU implementation: {e}")
            else:
                warnings.warn("Insufficient GPU memory for single GPU MAPEM. Falling back to CPU.")

        if result is None:
            try:
                result = MAPEM._MAPEM_CPU(SMatrix=SMatrix, y=y, Omega=self.potentialFunction, numIterations=self.numIterations, beta=self.beta, delta=self.delta, gamma=self.gamma, sigma=self.sigma, isSavingEachIteration=self.isSavingEachIteration, withTumor=withTumor)
            except Exception as e:
                warnings.warn(f"An error occurred in CPU implementation: {e}")
                result = None

        return result

    def _DEPIERRO(self, SMatrix, y, withTumor):
        """
        This method implements the DEPIERRO algorithm using either CPU or single-GPU PyTorch acceleration.
        Multi-GPU and Multi-CPU modes are not implemented for this algorithm.
        """
        result = None
        required_memory = calculate_memory_requirement(SMatrix, y)

        if self.isGPU:
            if check_gpu_memory(config.select_best_gpu(), required_memory):
                try:
                    result = DEPIERRO._DEPIERRO_GPU(SMatrix=SMatrix, y=y, numIterations=self.numIterations, beta=self.beta, sigma=self.sigma, isSavingEachIteration=self.isSavingEachIteration, withTumor=withTumor)
                except Exception as e:
                    warnings.warn(f"Falling back to CPU implementation due to an error in GPU implementation: {e}")
            else:
                warnings.warn("Insufficient GPU memory for single GPU DEPIERRO. Falling back to CPU.")

        if result is None:
            try:
                result = DEPIERRO._DEPIERRO_CPU(SMatrix=SMatrix, y=y, numIterations=self.numIterations, beta=self.beta, sigma=self.sigma, isSavingEachIteration=self.isSavingEachIteration, withTumor=withTumor)
            except Exception as e:
                warnings.warn(f"An error occurred in CPU implementation: {e}")
                result = None

        return result

