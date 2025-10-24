import numpy as np
import h5py
from pathos.multiprocessing import ProcessingPool
from .write_data import write_dataset_hdf5, create_group_hdf5
from .measure_w_lightcone import MeasureWLightcone
from .measure_m_lightcone import MeasureMultipolesLightcone


class MeasureJackknife(MeasureWLightcone,
					   MeasureMultipolesLightcone):
	"""Class that contains all methods for jackknife covariance measurements for IA correlation functions.

	Methods
	-------
	_measure_jackknife_realisations_obs()
		Measures all jackknife realisations for MeasureIALightcone using 1 or more CPUs.
	_measure_jackknife_covariance_obs()
		Combines jackknife realisations for MeasureIALightcone into covariance.
	_measure_jackknife_realisations_obs_multiprocessing()
		Measures all jackknife realisations for MeasureIALightcone using >1 CPU.
	measure_covariance_multiple_datasets()
		Given the jackknife realisations of two datasets, creates the cross covariance.
	create_full_cov_matrix_projections()
		Creates larger covariance matrix of multiple datasets including cross terms.

	Notes
	-----
	Inherits attributes from 'SimInfo', where 'boxsize', 'L_0p5' and 'snap_group' are used in this class.
	Inherits attributes from 'MeasureIABase', where 'data', 'output_file_name', 'periodicity', 'Num_position',
	'Num_shape', 'r_min', 'r_max', 'num_bins_r', 'num_bins_pi', 'r_bins', 'pi_bins', 'mu_r_bins' are used.
	"""

	def __init__(
			self,
			data,
			output_file_name,
			simulation=None,
			snapshot=None,
			separation_limits=[0.1, 20.0],
			num_bins_r=8,
			num_bins_pi=20,
			pi_max=None,
			boxsize=None,
			periodicity=True,
	):
		"""
		The __init__ method of the MeasureJackknife class.

		Notes
		-----
		Constructor parameters 'data', 'output_file_name', 'simulation', 'snapshot', 'separation_limits', 'num_bins_r',
		'num_bins_pi', 'pi_max', 'boxsize' and 'periodicity' are passed to MeasureIABase.

		"""
		super().__init__(data, output_file_name, simulation, snapshot, separation_limits, num_bins_r, num_bins_pi,
						 pi_max, boxsize, periodicity)
		return

	def _measure_jackknife_realisations_lightcone(
			self, patches_pos, patches_shape, corr_type, dataset_name, masks=None,
			rp_cut=None, over_h=False, cosmology=None, count_pairs=False, data_suffix="", num_sample_names=["S", "D"]
	):
		"""Measures the jackknife realisations for the projected correlation functions in MeasureIALightcone using the
		jackknife method. The area is already divided into patches; the correlation function is calculated omitting one
		patch at a time. This method uses 1 or more CPUs.

		Parameters
		----------
		patches_pos : ndarray
			Array with the patch numbers of each object in the position sample.
		patches_shape : ndarray
			Array with the patch numbers of each object in the shape sample.
		dataset_name : str
			Name of the dataset in the output file.
		corr_type : iterable with 2 str entries
			Array with two entries. For first choose from [gg, g+, both], for second from [w, multipoles].
		masks : dict or NoneType, optional
			See MeasureIALightcone methods. Default is None.
		rp_cut : float or NoneType, optional
			See MeasureIALightcone.measure_xi_multipoles. Default is None.
		over_h : bool, optional
			See MeasureIALightcone. Default value is False.
		cosmology : pyccl cosmology object or NoneType, optional
			See MeasureIALightcone. Default is None.
		count_pairs : bool, optional
			If True, only gg is measured, not g+. Default value is False.
		data_suffix : str, optional
			Addition to dataset name. Used to distinguish between DR,DD and RR measurements. Default value is "".
		num_sample_names : list with two entries, optional
			Keywords of the num_samples dictionary to access number of objects in position ond shape samples. Default
			value is ["S", "D"].

		Returns
		-------

		"""
		if count_pairs and data_suffix == "":
			raise ValueError("Enter a data suffix (like _DD) for your pair count.")
		figname_dataset_name = dataset_name
		if "/" in dataset_name:
			figname_dataset_name = figname_dataset_name.replace("/", "_")
		if "." in dataset_name:
			figname_dataset_name = figname_dataset_name.replace(".", "p")

		min_patch, max_patch = int(min(patches_pos)), int(max(patches_pos))
		num_patches = max_patch - min_patch + 1
		if min(patches_shape) != min_patch:
			print(
				"Warning! Minimum patch number of shape sample is not equal to minimum patch number of position sample.")
		if max(patches_shape) != max_patch:
			print(
				"Warning! Maximum patch number of shape sample is not equal to maximum patch number of position sample.")
		print(
			f"Calculating jackknife realisations for {num_patches} patches for {dataset_name}.")

		for i in np.arange(min_patch, max_patch + 1):
			mask_position = (patches_pos != i)
			mask_shape = (patches_shape != i)
			if masks != None:
				mask_position = mask_position * masks["Redshift"]
				mask_shape = mask_shape * masks["Redshift_shape_sample"]
			self.num_samples[f"{i}"][num_sample_names[0]] = sum(mask_shape)
			self.num_samples[f"{i}"][num_sample_names[1]] = sum(mask_position)
			masks_total = {
				"Redshift": mask_position,
				"Redshift_shape_sample": mask_shape,
				"RA": mask_position,
				"RA_shape_sample": mask_shape,
				"DEC": mask_position,
				"DEC_shape_sample": mask_shape,
				"e1": mask_shape,
				"e2": mask_shape,
				"weight": mask_position,
				"weight_shape_sample": mask_shape,
			}
			if corr_type[1] == "multipoles":
				if count_pairs:
					self._count_pairs_xi_r_mur_lightcone_brute(masks=masks_total,
															   dataset_name=dataset_name + "_" + str(i),
															   over_h=over_h, cosmology=cosmology, print_num=False,
															   data_suffix=data_suffix, rp_cut=rp_cut,
															   jk_group_name=f"{dataset_name}_jk{num_patches}")
				else:
					self._measure_xi_r_mur_lightcone_brute(
						masks=masks_total,
						rp_cut=rp_cut,
						dataset_name=dataset_name + "_" + str(i),
						print_num=False,
						over_h=over_h,
						cosmology=cosmology,
						jk_group_name=f"{dataset_name}_jk{num_patches}",
					)

			else:
				if count_pairs:
					self._count_pairs_xi_rp_pi_lightcone_brute(masks=masks_total,
															   dataset_name=dataset_name + "_" + str(i),
															   over_h=over_h, cosmology=cosmology, print_num=False,
															   data_suffix=data_suffix,
															   jk_group_name=f"{dataset_name}_jk{num_patches}")
				else:
					self._measure_xi_rp_pi_lightcone_brute(
						masks=masks_total,
						dataset_name=dataset_name + "_" + str(i),
						print_num=False,
						over_h=over_h,
						cosmology=cosmology,
						jk_group_name=f"{dataset_name}_jk{num_patches}",
					)
		return

	def _measure_jackknife_covariance_lightcone(
			self, IA_estimator, corr_type, dataset_name, max_patch, min_patch=1,
			randoms_suf="_randoms"
	):
		"""Combines the jackknife realisations measured with _measure_jackknife_realisations_obs or
		_measure_jackknife_realisations_obs_multiprocessing into a covariance.

		Parameters
		----------
		IA_estimator : str
			Choose which type of xi estimator is used. Choose from "clusters" or "galaxies".
		dataset_name : str
			Name of the dataset in the output file.
		corr_type : iterable with 2 str entries
			Array with two entries. For first choose from [gg, g+, both], for second from [w, multipoles].
		max_patch : int
			Maximum patch number used.
		min_patch : int, optional
			Minimum patch number used. Default value is 1.
		randoms_suf : str, optional
			Suffix used to denote the datasets that have been created using the randoms. Default value is "_randoms".

		Returns
		-------

		"""
		if corr_type[0] == "both":
			data = [corr_type[1] + "_g_plus", corr_type[1] + "_gg"]
		elif corr_type[0] == "g+":
			data = [corr_type[1] + "_g_plus"]
		elif corr_type[0] == "gg":
			data = [corr_type[1] + "_gg"]
		else:
			raise KeyError("Unknown value for corr_type. Choose from [g+, gg, both]")
		figname_dataset_name = dataset_name
		if "/" in dataset_name:
			figname_dataset_name = figname_dataset_name.replace("/", "_")
		if "." in dataset_name:
			figname_dataset_name = figname_dataset_name.replace(".", "p")
		num_patches = max_patch - min_patch + 1
		print(
			f"Calculating jackknife errors for {num_patches} patches for {dataset_name} with {dataset_name}{randoms_suf} as randoms.")

		covs, stds = [], []
		for d in np.arange(0, len(data)):
			for b in np.arange(min_patch, max_patch + 1):
				self._obs_estimator(corr_type, IA_estimator, f"{dataset_name}_{b}",
									f"{dataset_name}{randoms_suf}_{b}", self.num_samples[f"{b}"],
									jk_group_name=f"{dataset_name}_jk{num_patches}",
									jk_group_name_randoms=f"{dataset_name}{randoms_suf}_jk{num_patches}")
				if "w" in data[d]:
					self._measure_w_g_i(corr_type=corr_type[0], dataset_name=f"{dataset_name}_{b}",
										jk_group_name=f"{dataset_name}_jk{num_patches}")
				else:
					self._measure_multipoles(corr_type=corr_type[0], dataset_name=f"{dataset_name}_{b}",
											 jk_group_name=f"{dataset_name}_jk{num_patches}")

			data_file = h5py.File(self.output_file_name, "a")
			group_multipoles = data_file[f"{self.snap_group}/{data[d]}/{dataset_name}_jk{num_patches}"]
			# calculating mean of the datavectors
			mean_multipoles = np.zeros(self.num_bins_r)
			for b in np.arange(min_patch, max_patch + 1):
				mean_multipoles += group_multipoles[f"{dataset_name}_{b}"][:]
			mean_multipoles /= num_patches

			# calculation the covariance matrix (multipoles) and the standard deviation (sqrt of diag of cov)
			cov = np.zeros((self.num_bins_r, self.num_bins_r))
			std = np.zeros(self.num_bins_r)
			for b in np.arange(min_patch, max_patch + 1):
				correlation = group_multipoles[f"{dataset_name}_{b}"][:]
				std += (correlation - mean_multipoles) ** 2
				for i in np.arange(self.num_bins_r):
					cov[:, i] += (correlation - mean_multipoles) * (correlation[i] - mean_multipoles[i])

			std *= (num_patches - 1) / num_patches  # see Singh 2023
			std = np.sqrt(std)  # size of errorbars
			cov *= (num_patches - 1) / num_patches  # cov not sqrt so to get std, sqrt of diag would need to be taken
			data_file.close()
			if self.output_file_name != None:
				output_file = h5py.File(self.output_file_name, "a")
				group_multipoles = create_group_hdf5(output_file, f"{self.snap_group}/" + data[d])
				write_dataset_hdf5(group_multipoles, dataset_name + "_mean_" + str(num_patches), data=mean_multipoles)
				write_dataset_hdf5(group_multipoles, dataset_name + "_jackknife_" + str(num_patches), data=std)
				write_dataset_hdf5(group_multipoles, dataset_name + "_jackknife_cov_" + str(num_patches), data=cov)
				output_file.close()
			else:
				covs.append(cov)
				stds.append(std)
		if self.output_file_name != None:
			return
		else:
			return covs, stds

	def _measure_jackknife_realisations_lightcone_multiprocessing(
			self, patches_pos, patches_shape, corr_type, dataset_name, masks=None,
			rp_cut=None, over_h=False, num_nodes=4, cosmology=None, count_pairs=False, data_suffix="",
			num_sample_names=["S", "D"]
	):
		"""Measures the jackknife realisations for the projected correlation functions in MeasureIALightcone using the
		jackknife method. The area is already divided into patches; the correlation function is calculated omitting one
		patch at a time. This method uses >1 CPUs.

		Parameters
		----------
		patches_pos : ndarray
			Array with the patch numbers of each object in the position sample.
		patches_shape : ndarray
			Array with the patch numbers of each object in the shape sample.
		dataset_name : str
			Name of the dataset in the output file.
		corr_type : iterable with 2 str entries
			Array with two entries. For first choose from [gg, g+, both], for second from [w, multipoles].
		masks : dict or NoneType, optional
			See MeasureIALightcone methods. Default is None.
		rp_cut : float or NoneType, optional
			See MeasureIALightcone.measure_xi_multipoles. Default is None.
		over_h : bool, optional
			See MeasureIALightcone. Default value is False.
		num_nodes : int, optional
			Number of cores to be used in multiprocessing. Default is 4.
		cosmology : pyccl cosmology object or NoneType, optional
			See MeasureIALightcone. Default is None.
		count_pairs : bool, optional
			If True, only gg is measured, not g+. Default value is False.
		data_suffix : str, optional
			Addition to dataset name. Used to distinguish between DR,DD and RR measurements. Default value is "".
		num_sample_names : list with two entries, optional
			Keywords of the num_samples dictionary to access number of objects in position ond shape samples. Default
			value is ["S", "D"].


		Returns
		-------

		"""
		if num_nodes == 1:
			self._measure_jackknife_realisations_lightcone(patches_pos, patches_shape, masks, corr_type, dataset_name,
														   rp_cut, over_h, cosmology, count_pairs, data_suffix,
														   num_sample_names)
			return

		if count_pairs == False:
			corr_type[0] = "both"
		if corr_type[0] == "both":
			data = [corr_type[1] + "_g_plus", corr_type[1] + "_gg"]
			corr_type_suff = ["_g_plus", "_gg"]
			xi_suff = ["SplusD", "DD"]
		elif corr_type[0] == "g+":
			data = [corr_type[1] + "_g_plus"]
			corr_type_suff = ["_g_plus"]
			xi_suff = ["SplusD"]
		elif corr_type[0] == "gg":
			data = [corr_type[1] + "_gg"]
			corr_type_suff = ["_gg"]
			xi_suff = ["DD"]
		else:
			raise KeyError("Unknown value for first entry of corr_type. Choose from [g+, gg, both]")
		if corr_type[1] == "multipoles":
			bin_var_names = ["r", "mu_r"]
		elif corr_type[1] == "w":
			bin_var_names = ["rp", "pi"]
		else:
			raise KeyError("Unknown value for second entry of corr_type. Choose from [multipoles, w_g_plus]")
		min_patch, max_patch = int(min(patches_pos)), int(max(patches_pos))
		num_patches = max_patch - min_patch + 1
		if min(patches_shape) != min_patch:
			print(
				"Warning! Minimum patch number of shape sample is not equal to minimum patch number of position sample.")
		if max(patches_shape) != max_patch:
			print(
				"Warning! Maximum patch number of shape sample is not equal to maximum patch number of position sample.")
		args_xi_g_plus, args_multipoles, tree_args = [], [], []
		for i in np.arange(min_patch, max_patch + 1):
			mask_position = (patches_pos != i)
			mask_shape = (patches_shape != i)
			if masks != None:
				mask_position = mask_position * masks["Redshift"]
				mask_shape = mask_shape * masks["Redshift_shape_sample"]
			self.num_samples[f"{i}"][num_sample_names[0]] = sum(mask_shape)
			self.num_samples[f"{i}"][num_sample_names[1]] = sum(mask_position)
			masks_total = {
				"Redshift": mask_position,
				"Redshift_shape_sample": mask_shape,
				"RA": mask_position,
				"RA_shape_sample": mask_shape,
				"DEC": mask_position,
				"DEC_shape_sample": mask_shape,
				"e1": mask_shape,
				"e2": mask_shape,
				"weight": mask_position,
				"weight_shape_sample": mask_shape,
			}
			if corr_type[1] == "multipoles":
				args_xi_g_plus.append(
					(
						dataset_name + "_" + str(i),
						masks_total,
						True,
						False,
						over_h,
						cosmology,
						rp_cut,
						data_suffix
					)
				)
			else:
				args_xi_g_plus.append(
					(
						dataset_name + "_" + str(i),
						masks_total,
						True,
						False,
						over_h,
						cosmology,
						data_suffix
					)
				)

		args_xi_g_plus = np.array(args_xi_g_plus)
		multiproc_chuncks = np.array_split(np.arange(num_patches), np.ceil(num_patches / num_nodes))
		for chunck in multiproc_chuncks:
			chunck = np.array(chunck, dtype=int)
			if corr_type[1] == "multipoles":
				if count_pairs:
					result = ProcessingPool(nodes=len(chunck)).map(
						self._count_pairs_xi_r_mur_lightcone_brute,
						args_xi_g_plus[chunck][:, 0],
						args_xi_g_plus[chunck][:, 1],
						args_xi_g_plus[chunck][:, 2],
						args_xi_g_plus[chunck][:, 3],
						args_xi_g_plus[chunck][:, 4],
						args_xi_g_plus[chunck][:, 5],
						args_xi_g_plus[chunck][:, 6],
						args_xi_g_plus[chunck][:, 7],
					)
				else:
					result = ProcessingPool(nodes=len(chunck)).map(
						self._measure_xi_r_mur_lightcone_brute,
						args_xi_g_plus[chunck][:, 0],
						args_xi_g_plus[chunck][:, 1],
						args_xi_g_plus[chunck][:, 2],
						args_xi_g_plus[chunck][:, 3],
						args_xi_g_plus[chunck][:, 4],
						args_xi_g_plus[chunck][:, 5],
						args_xi_g_plus[chunck][:, 6],
					)
			else:
				if count_pairs:
					result = ProcessingPool(nodes=len(chunck)).map(
						self._count_pairs_xi_rp_pi_lightcone_brute,
						args_xi_g_plus[chunck][:, 0],
						args_xi_g_plus[chunck][:, 1],
						args_xi_g_plus[chunck][:, 2],
						args_xi_g_plus[chunck][:, 3],
						args_xi_g_plus[chunck][:, 4],
						args_xi_g_plus[chunck][:, 5],
						args_xi_g_plus[chunck][:, 6],
					)
				else:
					result = ProcessingPool(nodes=len(chunck)).map(
						self._measure_xi_rp_pi_lightcone_brute,
						args_xi_g_plus[chunck][:, 0],
						args_xi_g_plus[chunck][:, 1],
						args_xi_g_plus[chunck][:, 2],
						args_xi_g_plus[chunck][:, 3],
						args_xi_g_plus[chunck][:, 4],
						args_xi_g_plus[chunck][:, 5],
					)

			output_file = h5py.File(self.output_file_name, "a")
			if count_pairs:
				for i in np.arange(0, len(chunck)):
					for j, data_j in enumerate(data):
						group_xigplus = create_group_hdf5(
							output_file, f"{self.snap_group}/{corr_type[1]}/xi_gg/{dataset_name}_jk{num_patches}"
						)
						write_dataset_hdf5(group_xigplus, f"{dataset_name}_{chunck[i] + min_patch}{data_suffix}",
										   data=result[i][j])
						write_dataset_hdf5(
							group_xigplus, f"{dataset_name}_{chunck[i] + min_patch}_{bin_var_names[0]}",
							data=result[i][1]
						)
						write_dataset_hdf5(
							group_xigplus, f"{dataset_name}_{chunck[i] + min_patch}_{bin_var_names[1]}",
							data=result[i][2]
						)
			else:
				for i in np.arange(0, len(chunck)):
					for j, data_j in enumerate(data):
						group_xigplus = create_group_hdf5(
							output_file,
							f"{self.snap_group}/{corr_type[1]}/xi{corr_type_suff[j]}/{dataset_name}_jk{num_patches}"
						)
						write_dataset_hdf5(group_xigplus, f"{dataset_name}_{chunck[i] + min_patch}_{xi_suff[j]}",
										   data=result[i][j])
						write_dataset_hdf5(
							group_xigplus, f"{dataset_name}_{chunck[i] + min_patch}_{bin_var_names[0]}",
							data=result[i][2]
						)
						write_dataset_hdf5(
							group_xigplus, f"{dataset_name}_{chunck[i] + min_patch}_{bin_var_names[1]}",
							data=result[i][3]
						)
			# write_dataset_hdf5(group_xigplus, f"{dataset_name}_{chunck[i]}_sigmasq", data=result[i][3])
			output_file.close()

		# for i in np.arange(0, num_patches):
		# 	if corr_type[1] == "multipoles":
		# 		self.measure_multipoles(corr_type=args_multipoles[i, 0], dataset_name=args_multipoles[i, 1])
		# 	else:
		# 		self.measure_w_g_i(corr_type=args_multipoles[i, 0], dataset_name=args_multipoles[i, 1])
		return

	def measure_covariance_multiple_datasets(self, corr_type, dataset_names, num_box=27, return_output=False):
		"""Combines the jackknife measurements for different datasets into one covariance matrix.
		Author: Marta Garcia Escobar (starting from measure_jackknife methods); updated

		Parameters
		----------
		corr_type : str
			Which type of correlation is measured. Takes 'w_g_plus', 'w_gg', 'multipoles_g_plus' or 'multipoles_gg'.
		dataset_names : list of str
			List of the dataset names. If there is only one value, it calculates the covariance matrix with itself.
		num_box : int, optional
			Number of jackknife realisations. Default value is 27.
		return_output : bool, optional
			If True, the output will be returned instead of written to a file. Default value is False.

		Returns
		-------
		ndarray, ndarray
			covariance, standard deviation

		"""
		# check if corr_type is valid
		valid_corr_types = ["w_g_plus", "multipoles_g_plus", "w_gg", "multipoles_gg"]
		if corr_type not in valid_corr_types:
			raise ValueError("corr_type must be 'w_g_plus', 'w_gg', 'multipoles_g_plus' or 'multipoles_gg'.")

		data_file = h5py.File(self.output_file_name, "a")

		mean_list = []  # list of arrays

		for dataset_name in dataset_names:
			group = data_file[f"{self.snap_group}/{corr_type}/{dataset_name}_jk{num_box}"]
			mean_multipoles = np.zeros(self.num_bins_r)
			for b in np.arange(0, num_box):
				mean_multipoles += group[dataset_name + "_" + str(b)]
			mean_multipoles /= num_box
			mean_list.append(mean_multipoles)

		# calculation the covariance matrix and the standard deviation (sqrt of diag of cov)
		cov = np.zeros((self.num_bins_r, self.num_bins_r))
		std = np.zeros(self.num_bins_r)

		if len(dataset_names) == 1:  # covariance with itself
			dataset_name = dataset_names[0]
			group = data_file[f"{self.snap_group}/{corr_type}/{dataset_name}_jk{num_box}"]
			for b in np.arange(0, num_box):
				std += (group[dataset_name + "_" + str(b)] - mean_list[0]) ** 2
				for i in np.arange(self.num_bins_r):
					cov[:, i] += (group[dataset_name + "_" + str(b)] - mean_list[0]) * (
							group[dataset_name + "_" + str(b)][i] - mean_list[0][i]
					)
		elif len(dataset_names) == 2:
			group0 = data_file[f"{self.snap_group}/{corr_type}/{dataset_names[0]}_jk{num_box}"]
			group1 = data_file[f"{self.snap_group}/{corr_type}/{dataset_names[1]}_jk{num_box}"]
			for b in np.arange(0, num_box):
				std += (group0[dataset_names[0] + "_" + str(b)] - mean_list[0]) * (
						group1[dataset_names[1] + "_" + str(b)] - mean_list[1])
				for i in np.arange(self.num_bins_r):
					cov[:, i] += (group0[dataset_names[0] + "_" + str(b)] - mean_list[0]) * (
							group1[dataset_names[1] + "_" + str(b)][i] - mean_list[1][i]
					)
		else:
			raise KeyError("Too many datasets given, choose either 1 or 2")

		std *= (num_box - 1) / num_box  # see Singh 2023
		std = np.sqrt(std)  # size of errorbars
		cov *= (num_box - 1) / num_box  # cov not sqrt so to get std, sqrt of diag would need to be taken

		data_file.close()

		if (self.output_file_name != None) and (return_output == False):
			output_file = h5py.File(self.output_file_name, "a")
			group = create_group_hdf5(output_file, f"{self.snap_group}/{corr_type}")
			if len(dataset_names) == 2:
				write_dataset_hdf5(group, dataset_names[0] + "_" + dataset_names[1] + "_jackknife_cov_" + str(
					num_box), data=cov)
				write_dataset_hdf5(group,
								   dataset_names[0] + "_" + dataset_names[1] + "_jackknife_" + str(num_box),
								   data=std)

			else:
				write_dataset_hdf5(group, dataset_names[0] + "_jackknife_cov_" + str(num_box), data=cov)
				write_dataset_hdf5(group, dataset_names[0] + "_jackknife_" + str(num_box), data=std)
			output_file.close()
			return
		else:
			return cov, std

	def create_full_cov_matrix_projections(self, corr_type, dataset_names=["LOS_x", "LOS_y", "LOS_z"], num_box=27,
										   return_output=False):
		"""Function that creates the full covariance matrix for all 3 projections and combined covariance for 2
		projections by combining previously obtained jackknife information. Generalised from Marta Garcia Escobar's code.

		Parameters
		----------
		corr_type : str
			Which type of correlation is measured. Takes 'w_g_plus', 'w_gg', 'multipoles_g_plus' or 'multipoles_gg'.
		num_box : int, optional
			Number of jackknife realisations. Default value is 27.
		dataset_names : list of str
			Dataset names of projections to be combined. Default value is ["LOS_x","LOS_y","LOS_z"].
		return_output : bool, optional
			If True, the output will be returned instead of written to a file. Default value is False.

		Returns
		-------
		ndarrays
			covariance for 3 projections, covariance for x and y, covariance for x and z, covariance for y and z

		"""
		self.measure_covariance_multiple_datasets(corr_type=corr_type,
												  dataset_names=[dataset_names[0], dataset_names[1]], num_box=num_box)
		self.measure_covariance_multiple_datasets(corr_type=corr_type,
												  dataset_names=[dataset_names[0], dataset_names[2]], num_box=num_box)
		self.measure_covariance_multiple_datasets(corr_type=corr_type,
												  dataset_names=[dataset_names[1], dataset_names[2]], num_box=num_box)

		# import needed datasets
		output_file = h5py.File(self.output_file_name, "a")
		group = output_file[f"{self.snap_group}/{corr_type}"]

		# cov matrix between datasets
		cov_xx = group[f'{dataset_names[0]}_jackknife_cov_{num_box}'][:]
		cov_yy = group[f'{dataset_names[1]}_jackknife_cov_{num_box}'][:]
		cov_zz = group[f'{dataset_names[2]}_jackknife_cov_{num_box}'][:]
		cov_xy = group[f'{dataset_names[0]}_{dataset_names[1]}_jackknife_cov_{num_box}'][:]
		cov_yz = group[f'{dataset_names[0]}_{dataset_names[2]}_jackknife_cov_{num_box}'][:]
		cov_xz = group[f'{dataset_names[1]}_{dataset_names[2]}_jackknife_cov_{num_box}'][:]

		# 3 projections
		cov_top = np.concatenate((cov_xx, cov_xy, cov_xz), axis=1)
		cov_middle = np.concatenate((cov_xy.T, cov_yy, cov_yz), axis=1)  # cov_xy.T = cov_yx
		cov_bottom = np.concatenate((cov_xz.T, cov_yz.T, cov_zz), axis=1)
		cov3 = np.concatenate((cov_top, cov_middle, cov_bottom), axis=0)

		# all 2 projections
		cov_top = np.concatenate((cov_xx, cov_xy), axis=1)
		cov_middle = np.concatenate((cov_xy.T, cov_yy), axis=1)  # cov_xz.T = cov_zx
		cov2xy = np.concatenate((cov_top, cov_middle), axis=0)

		cov_top = np.concatenate((cov_xx, cov_xz), axis=1)
		cov_middle = np.concatenate((cov_xz.T, cov_zz), axis=1)  # cov_xz.T = cov_zx
		cov2xz = np.concatenate((cov_top, cov_middle), axis=0)

		cov_top = np.concatenate((cov_yy, cov_yz), axis=1)
		cov_middle = np.concatenate((cov_yz.T, cov_zz), axis=1)  # cov_xz.T = cov_zx
		cov2yz = np.concatenate((cov_top, cov_middle), axis=0)

		if return_output:
			return cov3, cov2xy, cov2xz, cov2yz
		else:
			write_dataset_hdf5(group,
							   f"{dataset_names[0]}_{dataset_names[1]}_{dataset_names[2]}_combined_jackknife_cov_{num_box}",
							   data=cov3)
			write_dataset_hdf5(group,
							   f'{dataset_names[0]}_{dataset_names[1]}_combined_jackknife_cov_{num_box}',
							   data=cov2xy)
			write_dataset_hdf5(group,
							   f'{dataset_names[0]}_{dataset_names[2]}_combined_jackknife_cov_{num_box}',
							   data=cov2xz)
			write_dataset_hdf5(group,
							   f'{dataset_names[1]}_{dataset_names[2]}_combined_jackknife_cov_{num_box}',
							   data=cov2yz)
			return


if __name__ == "__main__":
	pass
