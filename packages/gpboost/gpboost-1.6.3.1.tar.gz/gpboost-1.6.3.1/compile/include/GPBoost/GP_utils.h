/*!
* This file is part of GPBoost a C++ library for combining
*	boosting with Gaussian process and mixed effects models
*
* Copyright (c) 2020 - 2024 Fabio Sigrist and Tim Gyger. All rights reserved.
*
* Licensed under the Apache License Version 2.0. See LICENSE file in the project root for license information.
*/
#ifndef GPB_GP_UTIL_H_
#define GPB_GP_UTIL_H_
#include <memory>
#include <GPBoost/type_defs.h>
#include <GPBoost/utils.h>
#include <LightGBM/utils/log.h>
using LightGBM::Log;

namespace GPBoost {

	/*!
	* \brief Determine unique locations and map duplicates in coordinates to first occurance of unique locations
	* \param coords Coordinates
	* \param num_data Number of data points
	* \param[out] uniques Index of unique coordinates / points
	* \param[out] unique_idx Index that indicates for every data point the corresponding unique point. Used for constructing incidence matrix Z_ if there are duplicates
	*/
	void DetermineUniqueDuplicateCoords(const den_mat_t& coords,
		data_size_t num_data,
		std::vector<int>& uniques,
		std::vector<int>& unique_idx);

	/*!
	* \brief Determine unique locations and map duplicates in coordinates to first occurance of unique locations
	* \param coords Coordinates
	* \param num_data Number of data points
	* \param[out] uniques Index of unique coordinates / points
	* \param[out] unique_idx Index that indicates for every data point the corresponding unique point. Used for constructing incidence matrix Z_ if there are duplicates
	*/
	void DetermineUniqueDuplicateCoordsFast(const den_mat_t& coords,
		data_size_t num_data,
		std::vector<int>& uniques,
		std::vector<int>& unique_idx);

	/*!
	* \brief Calculate distance matrix (dense matrix)
	* \param coords1 First set of points
	* \param coords2 Second set of points
	* \param only_one_set_of_coords If true, coords1 == coords2, and dist is a symmetric square matrix
	* \param[out] dist Matrix of dimension coords2.rows() x coords1.rows() with distances between all pairs of points in coords1 and coords2 (rows in coords1 and coords2). Often, coords1 == coords2
	*/
	template <class T_mat, typename std::enable_if <std::is_same<den_mat_t, T_mat>::value>::type* = nullptr >
	void CalculateDistances(const den_mat_t& coords1,
		const den_mat_t& coords2,
		bool only_one_set_of_coords,
		den_mat_t& dist) {
		dist = den_mat_t(coords2.rows(), coords1.rows());
		dist.setZero();
#pragma omp parallel for schedule(static)
		for (int i = 0; i < coords2.rows(); ++i) {
			int first_j = 0;
			if (only_one_set_of_coords) {
				dist(i, i) = 0.;
				first_j = i + 1;
			}
			for (int j = first_j; j < coords1.rows(); ++j) {
				dist(i, j) = (coords2.row(i) - coords1.row(j)).lpNorm<2>();
			}
		}
		if (only_one_set_of_coords) {
			dist.triangularView<Eigen::StrictlyLower>() = dist.triangularView<Eigen::StrictlyUpper>().transpose();
		}
	}//end CalculateDistances (dense)
	template <class T_mat, typename std::enable_if <std::is_same<sp_mat_t, T_mat>::value || std::is_same<sp_mat_rm_t, T_mat>::value>::type* = nullptr >
	void CalculateDistances(const den_mat_t& coords1,
		const den_mat_t& coords2,
		bool only_one_set_of_coords,
		T_mat& dist) {
		std::vector<Triplet_t> triplets;
		int n_max_entry;
		if (only_one_set_of_coords) {
			n_max_entry = (int)(coords1.rows() - 1) * (int)coords2.rows();
		}
		else {
			n_max_entry = (int)coords1.rows() * (int)coords2.rows();
		}
		triplets.reserve(n_max_entry);
#pragma omp parallel for schedule(static)
		for (int i = 0; i < coords2.rows(); ++i) {
			int first_j = 0;
			if (only_one_set_of_coords) {
#pragma omp critical
				{
					triplets.emplace_back(i, i, 0.);
				}
				first_j = i + 1;
			}
			for (int j = first_j; j < coords1.rows(); ++j) {
				double dist_i_j = (coords2.row(i) - coords1.row(j)).lpNorm<2>();
#pragma omp critical
				{
					triplets.emplace_back(i, j, dist_i_j);
					if (only_one_set_of_coords) {
						triplets.emplace_back(j, i, dist_i_j);
					}
				}
			}
		}
		dist = T_mat(coords2.rows(), coords1.rows());
		dist.setFromTriplets(triplets.begin(), triplets.end());
		dist.makeCompressed();
	}//end CalculateDistances (sparse)

	/*!
	* \brief Calculate distance matrix when compactly supported covariance functions are used
	* \param coords1 First set of points
	* \param coords2 Second set of points
	* \param only_one_set_of_coords If true, coords1 == coords2, and dist is a symmetric square matrix
	* \param taper_range Range parameter of Wendland covariance function / taper beyond which the covariance is zero, and distances are thus not needed
	* \param show_number_non_zeros If true, the percentage of non-zero values is shown
	* \param[out] dist Matrix of dimension coords2.rows() x coords1.rows() with distances between all pairs of points in coords1 and coords2 (rows in coords1 and coords2). Often, coords1 == coords2
	*/
	template <class T_mat, typename std::enable_if <std::is_same<den_mat_t, T_mat>::value>::type* = nullptr >
	void CalculateDistancesTapering(const den_mat_t& coords1, //(this is a placeholder which is not used, only here for template compatibility)
		const den_mat_t& coords2,
		bool only_one_set_of_coords,
		double,
		bool,
		den_mat_t& dist) {
		CalculateDistances<T_mat>(coords1, coords2, only_one_set_of_coords, dist);
	}//end CalculateDistancesTapering (dense)
	template <class T_mat, typename std::enable_if <std::is_same<sp_mat_t, T_mat>::value || std::is_same<sp_mat_rm_t, T_mat>::value>::type* = nullptr >
	void CalculateDistancesTapering(const den_mat_t& coords1,
		const den_mat_t& coords2,
		bool only_one_set_of_coords,
		double taper_range,
		bool show_number_non_zeros,
		T_mat& dist) {
		std::vector<Triplet_t> triplets;
		int n_max_entry;
		if (only_one_set_of_coords) {
			n_max_entry = 30 * (int)coords1.rows();
		}
		else {
			n_max_entry = 10 * (int)coords1.rows() + 10 * (int)coords2.rows();
		}
		triplets.reserve(n_max_entry);
		//Sort along the sum of the coordinates
		int num_data;
		int dim_coords = (int)coords1.cols();
		double taper_range_square = taper_range * taper_range;
		if (only_one_set_of_coords) {
			num_data = (int)coords1.rows();
		}
		else {
			num_data = (int)(coords1.rows() + coords2.rows());
		}
		std::vector<double> coords_sum(num_data);
		std::vector<int> sort_sum(num_data);
		if (only_one_set_of_coords) {
#pragma omp parallel for schedule(static)
			for (int i = 0; i < num_data; ++i) {
				coords_sum[i] = coords1(i, Eigen::all).sum();
			}
		}
		else {
			den_mat_t coords_all(num_data, dim_coords);
			coords_all << coords2, coords1;
#pragma omp parallel for schedule(static)
			for (int i = 0; i < num_data; ++i) {
				coords_sum[i] = coords_all(i, Eigen::all).sum();
			}
		}
		SortIndeces<double>(coords_sum, sort_sum);
		std::vector<int> sort_inv_sum(num_data);
#pragma omp parallel for schedule(static)
		for (int i = 0; i < num_data; ++i) {
			sort_inv_sum[sort_sum[i]] = i;
		}
		// Search for and calculate distances that are smaller than taper_range
		//  using a fast approach based on results of Ra and Kim (1993)
#pragma omp parallel for schedule(static)
		for (int i = 0; i < coords2.rows(); ++i) {
			if (only_one_set_of_coords) {
#pragma omp critical
				{
					triplets.emplace_back(i, i, 0.);
				}
			}
			bool down = true;
			bool up = true;
			int up_i = sort_inv_sum[i];
			int down_i = sort_inv_sum[i];
			double smd, sed;
			while (up || down) {
				if (down_i == 0) {
					down = false;
				}
				if (up_i == (num_data - 1)) {
					up = false;
				}
				if (down) {
					down_i--;
					if ((only_one_set_of_coords && sort_sum[down_i] > i) ||
						(!only_one_set_of_coords && sort_sum[down_i] >= coords2.rows())) {
						smd = std::pow(coords_sum[sort_sum[down_i]] - coords_sum[i], 2);
						if (smd > dim_coords * taper_range_square) {
							down = false;
						}
						else {
							if (only_one_set_of_coords) {
								sed = (coords1(sort_sum[down_i], Eigen::all) - coords1(i, Eigen::all)).squaredNorm();
							}
							else {
								sed = (coords1(sort_sum[down_i] - coords2.rows(), Eigen::all) - coords2(i, Eigen::all)).squaredNorm();
							}
							if (sed < taper_range_square) {
								double dist_i_j = std::sqrt(sed);
#pragma omp critical
								{
									if (only_one_set_of_coords) {
										triplets.emplace_back(i, sort_sum[down_i], dist_i_j);
										triplets.emplace_back(sort_sum[down_i], i, dist_i_j);
									}
									else {
										triplets.emplace_back(i, sort_sum[down_i] - coords2.rows(), dist_i_j);
									}
								}
							}//end sed < taper_range_square
						}//end smd <= dim_coords * taper_range_square
					}
				}//end down
				if (up) {
					up_i++;
					if ((only_one_set_of_coords && sort_sum[up_i] > i) ||
						(!only_one_set_of_coords && sort_sum[up_i] >= coords2.rows())) {
						smd = std::pow(coords_sum[sort_sum[up_i]] - coords_sum[i], 2);
						if (smd > dim_coords * taper_range_square) {
							up = false;
						}
						else {
							if (only_one_set_of_coords) {
								sed = (coords1(sort_sum[up_i], Eigen::all) - coords1(i, Eigen::all)).squaredNorm();
							}
							else {
								sed = (coords1(sort_sum[up_i] - coords2.rows(), Eigen::all) - coords2(i, Eigen::all)).squaredNorm();
							}
							if (sed < taper_range_square) {
								double dist_i_j = std::sqrt(sed);
#pragma omp critical
								{
									if (only_one_set_of_coords) {
										triplets.emplace_back(i, sort_sum[up_i], dist_i_j);
										triplets.emplace_back(sort_sum[up_i], i, dist_i_j);
									}
									else {
										triplets.emplace_back(i, sort_sum[up_i] - coords2.rows(), dist_i_j);
									}
								}
							}//end sed < taper_range_square
						}//end smd <= dim_coords * taper_range_square
					}
				}//end up
			}//end while (up || down)
		}//end loop over data i

// Old, slow version
//#pragma omp parallel for schedule(static)
//		for (int i = 0; i < coords2.rows(); ++i) {
//			int first_j = 0;
//			if (only_one_set_of_coords) {
//#pragma omp critical
//				{
//					triplets.emplace_back(i, i, 0.);
//				}
//				first_j = i + 1;
//			}
//			for (int j = first_j; j < coords1.rows(); ++j) {
//				double dist_i_j = (coords2.row(i) - coords1.row(j)).lpNorm<2>();
//				if (dist_i_j < taper_range) {
//#pragma omp critical
//					{
//						triplets.emplace_back(i, j, dist_i_j);
//						if (only_one_set_of_coords) {
//							triplets.emplace_back(j, i, dist_i_j);
//						}
//					}
//				}
//			}
//		}
		
		dist = T_mat(coords2.rows(), coords1.rows());
		dist.setFromTriplets(triplets.begin(), triplets.end());
		dist.makeCompressed();
		if (show_number_non_zeros) {
			double prct_non_zero;
			int non_zeros = (int)dist.nonZeros();
			if (only_one_set_of_coords) {
				prct_non_zero = ((double)non_zeros) / coords1.rows() / coords1.rows() * 100.;
				int num_non_zero_row = non_zeros / (int)coords1.rows();
				Log::REInfo("Average number of non-zero entries per row in covariance matrix: %d (%g %%)", num_non_zero_row, prct_non_zero);
			}
			else {
				prct_non_zero = non_zeros / coords1.rows() / coords2.rows() * 100.;
				Log::REInfo("Number of non-zero entries in covariance matrix: %d (%g %%)", non_zeros, prct_non_zero);
			}
		}
	}//end CalculateDistancesTapering (sparse)

	/*!
	* \brief Subtract the inner product M^TM from a matrix Sigma
	* \param[out] Sigma Matrix from which M^TM is subtracted
	* \param M Matrix M
	* \param only_triangular true/false only compute triangular matrix
	*/
	template <class T_mat, typename std::enable_if <std::is_same<den_mat_t, T_mat>::value>::type* = nullptr >
	void SubtractInnerProdFromMat(T_mat& Sigma,
		const den_mat_t& M,
		bool only_triangular) {
		CHECK(Sigma.rows() == M.cols());
		CHECK(Sigma.cols() == M.cols());
#pragma omp parallel for schedule(static)
		for (int i = 0; i < Sigma.rows(); ++i) {
			for (int j = i; j < Sigma.cols(); ++j) {
				Sigma(i, j) -= M.col(i).dot(M.col(j));
				if (!only_triangular) {
					if (j > i) {
						Sigma(j, i) = Sigma(i, j);
					}
				}
			}
		}
	}//end SubtractInnerProdFromMat (dense)
	template <class T_mat, typename std::enable_if <std::is_same<sp_mat_t, T_mat>::value || std::is_same<sp_mat_rm_t, T_mat>::value>::type* = nullptr >
	void SubtractInnerProdFromMat(T_mat & Sigma,
		const den_mat_t & M,
		bool only_triangular) {
		CHECK(Sigma.rows() == M.cols());
		CHECK(Sigma.cols() == M.cols());
#pragma omp parallel for schedule(static)
		for (int k = 0; k < Sigma.outerSize(); ++k) {
			for (typename T_mat::InnerIterator it(Sigma, k); it; ++it) {
				int i = (int)it.row();
				int j = (int)it.col();
				if (i <= j) {
					it.valueRef() -= M.col(i).dot(M.col(j));
					if (!only_triangular) {
						if (i < j) {
							Sigma.coeffRef(j, i) = Sigma.coeff(i, j);
						}
					}
				}
			}
		}
	}//end SubtractInnerProdFromMat (sparse)

	/*!
	* \brief Subtract the product M1^T * M2 from a matrix Sigma
	* \param[out] Sigma Matrix from which M1^T * M2 is subtracted
	* \param M1 Matrix M1
	* \param M2 Matrix M2
	* \param only_triangular true/false only compute triangular matrix
	*/
	template <class T_mat, typename std::enable_if <std::is_same<den_mat_t, T_mat>::value>::type* = nullptr >
	void SubtractProdFromMat(T_mat& Sigma,
		const den_mat_t& M1,
		const den_mat_t& M2,
		bool only_triangular) {
		CHECK(Sigma.rows() == M1.cols());
		CHECK(Sigma.cols() == M2.cols());
#pragma omp parallel for schedule(static)
		for (int i = 0; i < Sigma.rows(); ++i) {
			for (int j = i; j < Sigma.cols(); ++j) {
				Sigma(i, j) -= M1.col(i).dot(M2.col(j));
				if (!only_triangular) {
					if (j > i) {
						Sigma(j, i) = Sigma(i, j);
					}
				}
			}
		}
	}//end SubtractProdFromMat (dense)
	template <class T_mat, typename std::enable_if <std::is_same<sp_mat_t, T_mat>::value || std::is_same<sp_mat_rm_t, T_mat>::value>::type* = nullptr >
	void SubtractProdFromMat(T_mat & Sigma,
		const den_mat_t & M1,
		const den_mat_t & M2,
		bool only_triangular) {
		CHECK(Sigma.rows() == M1.cols());
		CHECK(Sigma.cols() == M2.cols());
#pragma omp parallel for schedule(static)
		for (int k = 0; k < Sigma.outerSize(); ++k) {
			for (typename T_mat::InnerIterator it(Sigma, k); it; ++it) {
				int i = (int)it.row();
				int j = (int)it.col();
				if (i <= j) {
					it.valueRef() -= M1.col(i).dot(M2.col(j));
					if (!only_triangular) {
						if (i < j) {
							Sigma.coeffRef(j, i) = Sigma.coeff(i, j);
						}
					}
				}
			}
		}
	}//end SubtractProdFromMat (sparse)

	/*!
	* \brief Subtract the product M1^T * M2 from a matrix non square Sigma (prediction)
	* \param[out] Sigma Matrix from which M1^T * M2 is subtracted
	* \param M1 Matrix M1
	* \param M2 Matrix M2
	*/
	template <class T_mat, typename std::enable_if <std::is_same<den_mat_t, T_mat>::value>::type* = nullptr >
	void SubtractProdFromNonSqMat(T_mat& Sigma,
		const den_mat_t& M1,
		const den_mat_t& M2) {
		CHECK(Sigma.rows() == M1.cols());
		CHECK(Sigma.cols() == M2.cols());
#pragma omp parallel for schedule(static)
		for (int i = 0; i < Sigma.rows(); ++i) {
			for (int j = 0; j < Sigma.cols(); ++j) {
				Sigma(i, j) -= M1.col(i).dot(M2.col(j));
			}
		}
	}//end SubtractProdFromNonSqMat (dense)
	template <class T_mat, typename std::enable_if <std::is_same<sp_mat_t, T_mat>::value || std::is_same<sp_mat_rm_t, T_mat>::value>::type* = nullptr >
	void SubtractProdFromNonSqMat(T_mat & Sigma,
		const den_mat_t & M1,
		const den_mat_t & M2) {
		CHECK(Sigma.rows() == M1.cols());
		CHECK(Sigma.cols() == M2.cols());
#pragma omp parallel for schedule(static)
		for (int k = 0; k < Sigma.outerSize(); ++k) {
			for (typename T_mat::InnerIterator it(Sigma, k); it; ++it) {
				int i = (int)it.row();
				int j = (int)it.col();
				it.valueRef() -= M1.col(i).dot(M2.col(j));
			}
		}
	}//end SubtractProdFromNonSqMat (sparse)

	/*!
	* \brief Subtract the matrix from a matrix Sigma
	* \param[out] Sigma Matrix from which M is subtracted
	* \param M Matrix
	*/
	template <class T_mat, typename std::enable_if <std::is_same<den_mat_t, T_mat>::value>::type* = nullptr >
	void SubtractMatFromMat(T_mat& Sigma,
		const den_mat_t& M) {
#pragma omp parallel for schedule(static)
		for (int i = 0; i < Sigma.rows(); ++i) {
			for (int j = i; j < Sigma.cols(); ++j) {
				Sigma(i, j) -= M(i, j);
				if (j > i) {
					Sigma(j, i) = Sigma(i, j);
				}
			}
		}
	}//end SubtractMatFromMat (dense)
	template <class T_mat, typename std::enable_if <std::is_same<sp_mat_t, T_mat>::value || std::is_same<sp_mat_rm_t, T_mat>::value>::type* = nullptr >
	void SubtractMatFromMat(T_mat & Sigma,
		const den_mat_t & M) {
#pragma omp parallel for schedule(static)
		for (int k = 0; k < Sigma.outerSize(); ++k) {
			for (typename T_mat::InnerIterator it(Sigma, k); it; ++it) {
				int i = (int)it.row();
				int j = (int)it.col();
				if (i <= j) {
					it.valueRef() -= M(i, j);
					if (i < j) {
						Sigma.coeffRef(j, i) = Sigma.coeff(i, j);
					}
				}
			}
		}
	}//end SubtractMatFromMat (sparse)

	/*
	Calculate the smallest distance between each of the data points and any of the input means.
	* \param means data cluster means that determine the inducing points
	* \param data data coordinates
	* \param[out] distances smallest distance between each of the data points and any of the input means
	*/
	void closest_distance(const den_mat_t& means,
		const den_mat_t& data,
		vec_t& distances);

	/*
	This is an alternate initialization method based on the [kmeans++](https://en.wikipedia.org/wiki/K-means%2B%2B)
	initialization algorithm.
	* \param data data coordinates
	* \param k Size of inducing points
	* \param gen RNG
	* \param[out] means data cluster means that determine the inducing points
	*/
	void random_plusplus(const den_mat_t& data,
		int k,
		RNG_t& gen,
		den_mat_t& means);

	/*
	Calculate means based on data points and their cluster assignments.
	* \param data data coordinates
	* \param  clusters index of the mean each data point is closest to
	* \param[out] means data cluster means that determine the inducing points
	* \param[out] indices indices of closest data points to means
	*/
	void calculate_means(const den_mat_t& data,
		vec_t& clusters,
		den_mat_t& means,
		vec_t& indices);

	/*
	This implementation of k-means uses [Lloyd's Algorithm](https://en.wikipedia.org/wiki/Lloyd%27s_algorithm)
	with the [kmeans++](https://en.wikipedia.org/wiki/K-means%2B%2B) used for initializing the means.
	* \param data Coordinates / input features
	* \param k Number of cluster centers (usually = inducing points)
	* \param gen RNG
	* \param[out] means data cluster means that determine the inducing points
	* \param[out] max_int maximal number of iterations
	*/
	void kmeans_plusplus(const den_mat_t& data,
		int k,
		RNG_t& gen,
		den_mat_t& means,
		int max_it);

	/*
	Determines indices of data which is inside a ball with given radius around given point
	* \param data data coordinates
	* \param indices_start indices of data considered
	* \param radius radius of ball
	* \param mid centre of ball
	* \param[out] indices indices of data points inside ball
	*/
	void data_in_ball(const den_mat_t& data,
		const std::vector<int>& indices_start,
		double radius,
		const vec_t& mid,
		std::vector<int>& indices);

	/*
	CoverTree Algorithmus
	* \param data data coordinates
	* \param eps size of cover part
	* \param gen RNG
	* \param[out] means data cluster means that determine the inducing points
	*/
	void CoverTree(const den_mat_t& data,
		double eps,
		RNG_t& gen,
		den_mat_t& means);

}  // namespace GPBoost

#endif   // GPB_GP_UTIL_H_
