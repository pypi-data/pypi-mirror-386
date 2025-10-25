# Copyright Contributors to the OpenVDB Project
# SPDX-License-Identifier: Apache-2.0
#
import logging
import timeit

import polyscope as ps
import torch
from fvdb.utils.examples import load_dragon_mesh

from fvdb import Grid


def main():
    logging.basicConfig(level=logging.INFO)
    logging.addLevelName(logging.INFO, "\033[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO))
    device = torch.device("cuda", torch.cuda.current_device())
    dtype = torch.float32

    vox_size = 0.0025
    vox_origin = (0, 0, 0)

    p, n = load_dragon_mesh(skip_every=1, device=device, dtype=dtype)

    index = Grid.from_points(p, voxel_size=vox_size, origin=vox_origin)
    index_dual = index.dual_grid()

    logging.info("Splatting into grid...")
    start = timeit.default_timer()
    nsplat = index.splat_trilinear(p, n)
    if p.is_cuda:
        torch.cuda.synchronize()
    logging.info(f"Done in {timeit.default_timer() - start}s!")

    gp = index.ijk
    gd = index_dual.ijk
    gp = index.voxel_to_world(gp.type(dtype))
    gd = index_dual.voxel_to_world(gd.type(dtype))

    p, n = p.cpu(), n.cpu()
    nsplat = nsplat.cpu()
    gp, gd = gp.cpu(), gd.cpu()

    ps.init()
    ps.register_point_cloud("points", p, radius=0.00075)
    grid_pts = ps.register_point_cloud("vox coords", gp, radius=0.0005)

    grid_pts.add_vector_quantity("splatted normals", nsplat, enabled=True, length=0.05, radius=0.001)
    ps.show()


if __name__ == "__main__":
    main()
