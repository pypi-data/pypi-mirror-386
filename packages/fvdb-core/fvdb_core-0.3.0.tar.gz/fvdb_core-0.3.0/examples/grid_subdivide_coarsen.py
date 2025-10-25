# Copyright Contributors to the OpenVDB Project
# SPDX-License-Identifier: Apache-2.0
#
import uuid

import fvdb.viz as fviz
import numpy as np
import point_cloud_utils as pcu
import polyscope as ps
import torch
from fvdb.utils.examples import load_dragon_mesh

import fvdb


def visualize_grid(a: fvdb.GridBatch, offset: float):
    assert a.grid_count == 1
    mesh_a = pcu.voxel_grid_geometry(a.ijk[0].jdata.cpu().numpy(), a.voxel_sizes[0].cpu().numpy(), gap_fraction=0.1)
    ps.register_surface_mesh(
        str(uuid.uuid4()),
        mesh_a[0] + np.array([0.0, 0.0, offset]) - a.voxel_sizes[0].cpu().numpy()[None, :] / 2.0,
        mesh_a[1],
        enabled=True,
    )


if __name__ == "__main__":
    ps.init()
    ps.set_ground_plane_mode("shadow_only")
    ps.set_navigation_style("free")

    [p] = load_dragon_mesh(mode="v", device=torch.device("cuda", torch.cuda.current_device()))

    grid_origin = fvdb.GridBatch.from_points(fvdb.JaggedTensor(p), voxel_sizes=[0.005] * 3, origins=[0.0] * 3)
    visualize_grid(grid_origin, 0.0)

    grid_refined = grid_origin.refined_grid(2)
    visualize_grid(grid_refined, 0.15)

    grid_coarsened = grid_origin.coarsened_grid(2)
    visualize_grid(grid_coarsened, 0.3)

    ps.show()

    grid_dual = grid_origin.dual_grid()

    grid_dual_gv, grid_dual_ge = fviz.gridbatch_edge_network(grid_dual)
    ps.remove_all_structures()
    visualize_grid(grid_origin, 0.0)
    ps.register_curve_network(
        str(uuid.uuid4()),
        grid_dual_gv[0].jdata.cpu().numpy(),
        grid_dual_ge[0].jdata.cpu().numpy(),
        enabled=True,
        radius=0.004,
    )
    ps.show()
