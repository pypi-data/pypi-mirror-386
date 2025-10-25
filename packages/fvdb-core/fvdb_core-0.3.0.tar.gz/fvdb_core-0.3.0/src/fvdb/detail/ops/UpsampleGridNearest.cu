// Copyright Contributors to the OpenVDB Project
// SPDX-License-Identifier: Apache-2.0
//
#include <fvdb/detail/ops/UpsampleGridNearest.h>
#include <fvdb/detail/utils/AccessorHelpers.cuh>
#include <fvdb/detail/utils/ForEachCPU.h>
#include <fvdb/detail/utils/cuda/ForEachCUDA.cuh>
#include <fvdb/detail/utils/cuda/ForEachPrivateUse1.cuh>

#include <THC/THCAtomics.cuh>
#include <c10/cuda/CUDAException.h>

namespace fvdb {
namespace detail {
namespace ops {

template <typename Dtype, template <typename T, int32_t D> typename TensorAccessor>
__hostdev__ inline void
upsampleNearestVoxelCallback(int32_t batchIdx,
                             int32_t leafIdx,
                             int32_t voxelIdx,
                             int32_t channelIdx,
                             GridBatchImpl::Accessor coarseBatchAccessor,
                             GridBatchImpl::Accessor fineBatchAccessor,
                             const TensorAccessor<Dtype, 2> coarseData, // [B*N, C]
                             TensorAccessor<Dtype, 2> outFineData,      // [B*N, C]
                             nanovdb::Coord upsamplingFactor) {
    const nanovdb::OnIndexGrid *coarseGrid = coarseBatchAccessor.grid(batchIdx);
    const nanovdb::OnIndexGrid *fineGrid   = fineBatchAccessor.grid(batchIdx);

    const typename nanovdb::OnIndexGrid::LeafNodeType &fineLeaf =
        fineGrid->tree().template getFirstNode<0>()[leafIdx];

    const auto coarseGridAcc       = coarseGrid->getAccessor();
    const int64_t fineBaseOffset   = fineBatchAccessor.voxelOffset(batchIdx);
    const int64_t coarseBaseOffset = coarseBatchAccessor.voxelOffset(batchIdx);

    const int64_t fineVoxelIndex = fineLeaf.getValue(voxelIdx);

    if (fineVoxelIndex == 0) {
        return;
    }

    const nanovdb::Coord fineIjk = fineLeaf.offsetToGlobalCoord(voxelIdx);
    const nanovdb::Coord coarseIjk =
        nanovdb::math::Vec3<Dtype>((Dtype)fineIjk[0] / (Dtype)upsamplingFactor[0],
                                   (Dtype)fineIjk[1] / (Dtype)upsamplingFactor[1],
                                   (Dtype)fineIjk[2] / (Dtype)upsamplingFactor[2])
            .floor();
    const int64_t coarseIndex =
        coarseGridAcc.getValue(coarseIjk) - static_cast<int64_t>(1) + coarseBaseOffset;
    const int64_t fineIndex = fineVoxelIndex - 1 + fineBaseOffset;

    if (coarseGridAcc.isActive(coarseIjk)) {
        outFineData[fineIndex][channelIdx] = coarseData[coarseIndex][channelIdx];
    }
}

template <typename Dtype,
          torch::DeviceType DeviceTag,
          template <typename T, int32_t D>
          typename TensorAccessor>
__hostdev__ inline void
upsampleNearestBackwardsVoxelCallback(int32_t batchIdx,
                                      int32_t leafIdx,
                                      int32_t voxelIdx,
                                      int32_t channelIdx,
                                      GridBatchImpl::Accessor coarseBatchAccessor,
                                      GridBatchImpl::Accessor fineBatchAccessor,
                                      const TensorAccessor<Dtype, 2> fineData, // [B*N, C]
                                      TensorAccessor<Dtype, 2> outCoarseData,  // [B*N, C]
                                      nanovdb::Coord upsamplingFactor) {
    const nanovdb::OnIndexGrid *coarseGrid = coarseBatchAccessor.grid(batchIdx);
    const nanovdb::OnIndexGrid *fineGrid   = fineBatchAccessor.grid(batchIdx);

    const typename nanovdb::OnIndexGrid::LeafNodeType &fineLeaf =
        fineGrid->tree().template getFirstNode<0>()[leafIdx];

    const auto coarseGridAcc       = coarseGrid->getAccessor();
    const int64_t fineBaseOffset   = fineBatchAccessor.voxelOffset(batchIdx);
    const int64_t coarseBaseOffset = coarseBatchAccessor.voxelOffset(batchIdx);

    const int64_t fineVoxelIndex = fineLeaf.getValue(voxelIdx);

    if (fineVoxelIndex == 0) {
        return;
    }

    const nanovdb::Coord fineIjk = fineLeaf.offsetToGlobalCoord(voxelIdx);
    const nanovdb::Coord coarseIjk =
        nanovdb::math::Vec3<Dtype>((Dtype)fineIjk[0] / (Dtype)upsamplingFactor[0],
                                   (Dtype)fineIjk[1] / (Dtype)upsamplingFactor[1],
                                   (Dtype)fineIjk[2] / (Dtype)upsamplingFactor[2])
            .floor();
    const int64_t coarseIndex =
        coarseGridAcc.getValue(coarseIjk) - static_cast<int64_t>(1) + coarseBaseOffset;
    const int64_t fineIndex = fineVoxelIndex - 1 + fineBaseOffset;

    if (coarseGridAcc.isActive(coarseIjk)) {
        if constexpr (DeviceTag == torch::kCUDA) {
            gpuAtomicAddNoReturn(&outCoarseData[coarseIndex][channelIdx],
                                 fineData[fineIndex][channelIdx]);
        } else {
            // FIXME: (@fwilliams) Atomics
            outCoarseData[coarseIndex][channelIdx] += fineData[fineIndex][channelIdx];
        }
    }
}

template <torch::DeviceType DeviceTag>
torch::Tensor
UpsampleGridNearest(const GridBatchImpl &coarseBatchAccessor,
                    const GridBatchImpl &fineBatchAccessor,
                    const torch::Tensor &coarseData,
                    nanovdb::Coord upsamplingFactor) {
    coarseBatchAccessor.checkNonEmptyGrid();
    fineBatchAccessor.checkNonEmptyGrid();

    for (int i = 0; i < 3; i += 1) {
        TORCH_CHECK(upsamplingFactor[i] > 0, "upsampling_factor must be greater than 0");
    }
    TORCH_CHECK(coarseData.dim() > 1,
                "coarse_data must have more than one dimension. i.e. have shape (num_voxels, *)");
    TORCH_CHECK(coarseData.size(0) == (int64_t)coarseBatchAccessor.totalVoxels(),
                "coarse_data must have the same number of voxels as coarse_grid");

    const int64_t numOutputValues = fineBatchAccessor.totalVoxels();
    auto opts = torch::TensorOptions().dtype(coarseData.dtype()).device(coarseData.device());
    torch::Tensor outFineData = torch::zeros(spliceShape({numOutputValues}, coarseData), opts);

    torch::Tensor coarseDataReshape  = featureCoalescedView(coarseData);
    torch::Tensor outFineDataReshape = featureCoalescedView(outFineData);
    TORCH_CHECK(outFineDataReshape.is_contiguous(),
                "out_fine_data must be contiguous. This should never happen");

    AT_DISPATCH_V2(
        coarseData.scalar_type(),
        "UpsampleGridNearest",
        AT_WRAP([&]() {
            auto coarseBatchAcc = gridBatchAccessor<DeviceTag>(coarseBatchAccessor);
            auto coarseDataAcc = tensorAccessor<DeviceTag, scalar_t, 2, int64_t>(coarseDataReshape);
            auto outFineDataAcc =
                tensorAccessor<DeviceTag, scalar_t, 2, int64_t>(outFineDataReshape);

            if constexpr (DeviceTag == torch::kCUDA) {
                auto callback = [=] __device__(int32_t batchIdx,
                                               int32_t leafIdx,
                                               int32_t voxelIdx,
                                               int32_t channelIdx,
                                               GridBatchImpl::Accessor fineBatchAccessor) {
                    upsampleNearestVoxelCallback<scalar_t, TorchRAcc64>(batchIdx,
                                                                        leafIdx,
                                                                        voxelIdx,
                                                                        channelIdx,
                                                                        coarseBatchAcc,
                                                                        fineBatchAccessor,
                                                                        coarseDataAcc,
                                                                        outFineDataAcc,
                                                                        upsamplingFactor);
                };
                forEachVoxelCUDA(640, outFineData.size(1), fineBatchAccessor, callback);
            } else if constexpr (DeviceTag == torch::kPrivateUse1) {
                auto callback = [=] __device__(int32_t batchIdx,
                                               int32_t leafIdx,
                                               int32_t voxelIdx,
                                               int32_t channelIdx,
                                               GridBatchImpl::Accessor fineBatchAccessor) {
                    upsampleNearestVoxelCallback<scalar_t, TorchRAcc64>(batchIdx,
                                                                        leafIdx,
                                                                        voxelIdx,
                                                                        channelIdx,
                                                                        coarseBatchAcc,
                                                                        fineBatchAccessor,
                                                                        coarseDataAcc,
                                                                        outFineDataAcc,
                                                                        upsamplingFactor);
                };
                forEachVoxelPrivateUse1(outFineData.size(1), fineBatchAccessor, callback);
            } else {
                auto callback = [=](int32_t batchIdx,
                                    int32_t leafIdx,
                                    int32_t voxelIdx,
                                    int32_t channelIdx,
                                    GridBatchImpl::Accessor fineBatchAccessor) {
                    upsampleNearestVoxelCallback<scalar_t, TorchAcc>(batchIdx,
                                                                     leafIdx,
                                                                     voxelIdx,
                                                                     channelIdx,
                                                                     coarseBatchAcc,
                                                                     fineBatchAccessor,
                                                                     coarseDataAcc,
                                                                     outFineDataAcc,
                                                                     upsamplingFactor);
                };
                forEachVoxelCPU(outFineData.size(1), fineBatchAccessor, callback);
            }
        }),
        AT_EXPAND(AT_FLOATING_TYPES),
        c10::kHalf,
        c10::kBFloat16);

    return outFineData;
}

template <torch::DeviceType DeviceTag>
torch::Tensor
UpsampleGridNearestBackward(const GridBatchImpl &fineBatchAccessor,
                            const GridBatchImpl &coarseBatchAccessor,
                            const torch::Tensor &gradOut,
                            const torch::Tensor &coarseData,
                            nanovdb::Coord upsamplingFactor) {
    for (int i = 0; i < 3; i += 1) {
        TORCH_CHECK(upsamplingFactor[i] > 0, "upsampling_factor must be greater than 0");
    }

    torch::Tensor coarseDataReshape = featureCoalescedView(coarseData);
    torch::Tensor gradOutReshape    = featureCoalescedView(gradOut);
    torch::Tensor outGradInReshape  = torch::zeros_like(coarseDataReshape);

    AT_DISPATCH_V2(
        gradOut.scalar_type(),
        "UpsampleGridNearestBackward",
        AT_WRAP([&]() {
            auto coarseBatchAcc = gridBatchAccessor<DeviceTag>(coarseBatchAccessor);
            auto gradOutAcc     = tensorAccessor<DeviceTag, scalar_t, 2, int64_t>(gradOutReshape);
            auto outCoarseDataAcc =
                tensorAccessor<DeviceTag, scalar_t, 2, int64_t>(outGradInReshape);

            if constexpr (DeviceTag == torch::kCUDA) {
                auto callback = [=] __device__(int32_t batchIdx,
                                               int32_t leafIdx,
                                               int32_t voxelIdx,
                                               int32_t channelIdx,
                                               GridBatchImpl::Accessor fineBatchAccessor) {
                    upsampleNearestBackwardsVoxelCallback<scalar_t, DeviceTag, TorchRAcc64>(
                        batchIdx,
                        leafIdx,
                        voxelIdx,
                        channelIdx,
                        coarseBatchAcc,
                        fineBatchAccessor,
                        gradOutAcc,
                        outCoarseDataAcc,
                        upsamplingFactor);
                };
                forEachVoxelCUDA(640, outGradInReshape.size(1), fineBatchAccessor, callback);
            } else if constexpr (DeviceTag == torch::kPrivateUse1) {
                auto callback = [=] __device__(int32_t batchIdx,
                                               int32_t leafIdx,
                                               int32_t voxelIdx,
                                               int32_t channelIdx,
                                               GridBatchImpl::Accessor fineBatchAccessor) {
                    upsampleNearestBackwardsVoxelCallback<scalar_t, DeviceTag, TorchRAcc64>(
                        batchIdx,
                        leafIdx,
                        voxelIdx,
                        channelIdx,
                        coarseBatchAcc,
                        fineBatchAccessor,
                        gradOutAcc,
                        outCoarseDataAcc,
                        upsamplingFactor);
                };
                forEachVoxelPrivateUse1(outGradInReshape.size(1), fineBatchAccessor, callback);
            } else {
                auto callback = [=](int32_t batchIdx,
                                    int32_t leafIdx,
                                    int32_t voxelIdx,
                                    int32_t channelIdx,
                                    GridBatchImpl::Accessor fineBatchAccessor) {
                    upsampleNearestBackwardsVoxelCallback<scalar_t, DeviceTag, TorchAcc>(
                        batchIdx,
                        leafIdx,
                        voxelIdx,
                        channelIdx,
                        coarseBatchAcc,
                        fineBatchAccessor,
                        gradOutAcc,
                        outCoarseDataAcc,
                        upsamplingFactor);
                };
                forEachVoxelCPU(outGradInReshape.size(1), fineBatchAccessor, callback);
            }
        }),
        AT_EXPAND(AT_FLOATING_TYPES),
        c10::kHalf,
        c10::kBFloat16);

    torch::Tensor outGradIn = outGradInReshape.reshape(spliceShape({coarseData.size(0)}, gradOut));
    TORCH_CHECK(outGradIn.is_contiguous(),
                "out_grad_in must be contiguous. This should never happen");
    return outGradIn;
}

template <torch::DeviceType DeviceTag>
torch::Tensor
dispatchUpsampleGridNearest<DeviceTag>(const GridBatchImpl &coarseBatchAccessor,
                                       const GridBatchImpl &fineBatchAccessor,
                                       const torch::Tensor &coarseData,
                                       nanovdb::Coord upsamplingFactor) {
    return UpsampleGridNearest<DeviceTag>(
        coarseBatchAccessor, fineBatchAccessor, coarseData, upsamplingFactor);
}

template <torch::DeviceType DeviceTag>
torch::Tensor
dispatchUpsampleGridNearestBackward<DeviceTag>(const GridBatchImpl &fineBatchAccessor,
                                               const GridBatchImpl &coarseBatchAccessor,
                                               const torch::Tensor &gradOut,
                                               const torch::Tensor &coarseData,
                                               nanovdb::Coord upsamplingFactor) {
    return UpsampleGridNearestBackward<DeviceTag>(
        fineBatchAccessor, coarseBatchAccessor, gradOut, coarseData, upsamplingFactor);
}

template torch::Tensor dispatchUpsampleGridNearest<torch::kCPU>(const GridBatchImpl &,
                                                                const GridBatchImpl &,
                                                                const torch::Tensor &,
                                                                nanovdb::Coord);
template torch::Tensor dispatchUpsampleGridNearest<torch::kCUDA>(const GridBatchImpl &,
                                                                 const GridBatchImpl &,
                                                                 const torch::Tensor &,
                                                                 nanovdb::Coord);
template torch::Tensor dispatchUpsampleGridNearest<torch::kPrivateUse1>(const GridBatchImpl &,
                                                                        const GridBatchImpl &,
                                                                        const torch::Tensor &,
                                                                        nanovdb::Coord);

template torch::Tensor dispatchUpsampleGridNearestBackward<torch::kCPU>(const GridBatchImpl &,
                                                                        const GridBatchImpl &,
                                                                        const torch::Tensor &,
                                                                        const torch::Tensor &,
                                                                        nanovdb::Coord);
template torch::Tensor dispatchUpsampleGridNearestBackward<torch::kCUDA>(const GridBatchImpl &,
                                                                         const GridBatchImpl &,
                                                                         const torch::Tensor &,
                                                                         const torch::Tensor &,
                                                                         nanovdb::Coord);
template torch::Tensor
dispatchUpsampleGridNearestBackward<torch::kPrivateUse1>(const GridBatchImpl &,
                                                         const GridBatchImpl &,
                                                         const torch::Tensor &,
                                                         const torch::Tensor &,
                                                         nanovdb::Coord);

} // namespace ops
} // namespace detail
} // namespace fvdb
