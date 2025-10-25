// Copyright Contributors to the OpenVDB Project
// SPDX-License-Identifier: Apache-2.0
//
#ifndef FVDB_DETAIL_OPS_GSPLAT_GAUSSIANRASTERIZETOPCONTRIBUTINGGAUSSIANIDS_H
#define FVDB_DETAIL_OPS_GSPLAT_GAUSSIANRASTERIZETOPCONTRIBUTINGGAUSSIANIDS_H

#include <fvdb/JaggedTensor.h>
#include <fvdb/detail/ops/gsplat/GaussianRenderSettings.h>

#include <torch/types.h>

#include <tuple>

namespace fvdb {
namespace detail {
namespace ops {

/// @brief Performs deep image rasterization to render the IDs and weighted alpha values of the
/// top-K most visible Gaussians for each pixel
template <torch::DeviceType>
std::tuple<torch::Tensor, torch::Tensor> dispatchGaussianRasterizeTopContributingGaussianIds(
    const torch::Tensor &means2d,           // [C, N, 2]
    const torch::Tensor &conics,            // [C, N, 3]
    const torch::Tensor &opacities,         // [N]
    const torch::Tensor &tile_offsets,      // [C, tile_height, tile_width]
    const torch::Tensor &tile_gaussian_ids, // [n_isects]
    const RenderSettings &settings);

/// @brief Performs sparse deep image rasterization to render the IDs and weighted alpha values of
/// the top-K most visible Gaussians for each pixel. Renders only specified pixels.
template <torch::DeviceType>
std::tuple<fvdb::JaggedTensor, fvdb::JaggedTensor>
dispatchGaussianSparseRasterizeTopContributingGaussianIds(
    const torch::Tensor &means2d,           // [C, N, 2]
    const torch::Tensor &conics,            // [C, N, 3]
    const torch::Tensor &opacities,         // [N]
    const torch::Tensor &tile_offsets,      // [C, tile_height, tile_width]
    const torch::Tensor &tile_gaussian_ids, // [n_isects]
    const fvdb::JaggedTensor &pixelsToRender,
    const torch::Tensor &activeTiles,
    const torch::Tensor &tilePixelMask,
    const torch::Tensor &tilePixelCumsum,
    const torch::Tensor &pixelMap,
    const RenderSettings &settings);

} // namespace ops
} // namespace detail
} // namespace fvdb

#endif // FVDB_DETAIL_OPS_GSPLAT_GAUSSIANRASTERIZETOPCONTRIBUTINGGAUSSIANIDS_H
