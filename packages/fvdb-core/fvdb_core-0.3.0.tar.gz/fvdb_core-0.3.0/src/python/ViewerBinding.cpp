// Copyright Contributors to the OpenVDB Project
// SPDX-License-Identifier: Apache-2.0
//
#include "TypeCasters.h"

#include <fvdb/GaussianSplat3d.h>
#include <fvdb/detail/viewer/CameraView.h>
#include <fvdb/detail/viewer/GaussianSplat3dView.h>
#include <fvdb/detail/viewer/Viewer.h>

#include <pybind11/pytypes.h>
#include <pybind11/stl.h>

void
bind_viewer(py::module &m) {
    py::class_<fvdb::detail::viewer::CameraView>(
        m, "CameraView", "A view object for visualizing a camera in the editor")
        .def_property("visible",
                      &fvdb::detail::viewer::CameraView::getVisible,
                      &fvdb::detail::viewer::CameraView::setVisible,
                      "Whether the camera view is visible")
        .def_property_readonly(
            "name", &fvdb::detail::viewer::CameraView::getName, "The name of this camera view")
        .def_property("axis_length",
                      &fvdb::detail::viewer::CameraView::getAxisLength,
                      &fvdb::detail::viewer::CameraView::setAxisLength,
                      "The axis length for the gizmo")
        .def_property("axis_thickness",
                      &fvdb::detail::viewer::CameraView::getAxisThickness,
                      &fvdb::detail::viewer::CameraView::setAxisThickness,
                      "The axis thickness for the gizmo")
        .def_property("frustum_line_width",
                      &fvdb::detail::viewer::CameraView::getFrustumLineWidth,
                      &fvdb::detail::viewer::CameraView::setFrustumLineWidth,
                      "The line width of the frustum")
        .def_property("frustum_scale",
                      &fvdb::detail::viewer::CameraView::getFrustumScale,
                      &fvdb::detail::viewer::CameraView::setFrustumScale,
                      "The scale of the frustum visualization, default is 1.0")
        .def_property(
            "frustum_color",
            &fvdb::detail::viewer::CameraView::getFrustumColor,
            [](fvdb::detail::viewer::CameraView &self, const std::tuple<float, float, float> &rgb) {
                self.setFrustumColor(std::get<0>(rgb), std::get<1>(rgb), std::get<2>(rgb));
            },
            "The RGB color of the frustum as a 3-tuple");

    py::class_<fvdb::detail::viewer::GaussianSplat3dView>(
        m, "GaussianSplat3dView", "A view for displaying Gaussian splat 3D data in the viewer")
        .def_property("tile_size",
                      &fvdb::detail::viewer::GaussianSplat3dView::getTileSize,
                      &fvdb::detail::viewer::GaussianSplat3dView::setTileSize,
                      "The tile size for rendering this Gaussian scene.")
        .def_property(
            "min_radius_2d",
            &fvdb::detail::viewer::GaussianSplat3dView::getMinRadius2d,
            &fvdb::detail::viewer::GaussianSplat3dView::setMinRadius2d,
            "The minimum projected pixel radius below which Gaussians will not be rendered.")
        .def_property("eps_2d",
                      &fvdb::detail::viewer::GaussianSplat3dView::getEps2d,
                      &fvdb::detail::viewer::GaussianSplat3dView::setEps2d,
                      "The 2D epsilon value for this Gaussian scene.")
        .def_property("antialias",
                      &fvdb::detail::viewer::GaussianSplat3dView::getAntialias,
                      &fvdb::detail::viewer::GaussianSplat3dView::setAntialias,
                      "Whether to enable antialiasing for this Gaussian scene.")
        .def_property(
            "sh_degree_to_use",
            &fvdb::detail::viewer::GaussianSplat3dView::getShDegreeToUse,
            &fvdb::detail::viewer::GaussianSplat3dView::setShDegreeToUse,
            "The spherical harmonics degree used to render this Gaussian scene. A value of 0 means all available spherical harmonics are used.")
        .def_property("rgb_rgb_rgb_sh",
                      &fvdb::detail::viewer::GaussianSplat3dView::isShStrideRgbRgbRgb,
                      &fvdb::detail::viewer::GaussianSplat3dView::setShStrideRgbRgbRgb,
                      "Whether the spherical harmonics data is stored in RGBRGB... order.");

    py::class_<fvdb::detail::viewer::Viewer>(
        m, "Viewer", "A viewer for displaying 3D data including Gaussian splats")
        .def(py::init<const std::string &, const int, const int, const bool>(),
             py::arg("ip_address"),
             py::arg("port"),
             py::arg("device_id"),
             py::arg("verbose"),
             "Create a new Viewer instance")
        .def(
            "add_gaussian_splat_3d_view",
            &fvdb::detail::viewer::Viewer::addGaussianSplat3dView,
            py::arg("scene_name"),
            py::arg("name"),
            py::arg("gaussian_splat_3d"),
            py::return_value_policy::reference_internal, // preserve reference; tie lifetime to
                                                         // parent
            "Register a Gaussian splat 3D view with the viewer (accepts Python or C++ GaussianSplat3d)")
        .def("has_gaussian_splat_3d_view",
             &fvdb::detail::viewer::Viewer::hasGaussianSplat3dView,
             py::arg("name"),
             "Check if a Gaussian splat 3D view with the given name exists")
        .def("get_gaussian_splat_3d_view",
             &fvdb::detail::viewer::Viewer::getGaussianSplat3dView,
             py::arg("name"),
             py::return_value_policy::reference_internal,
             "Get a Gaussian splat 3D view by name")

        .def("ip_address",
             &fvdb::detail::viewer::Viewer::ipAddress,
             "The IP address the viewer server is listening on.")

        .def("port",
             &fvdb::detail::viewer::Viewer::port,
             "The port the viewer server is listening on.")

        .def("reset", &fvdb::detail::viewer::Viewer::reset, "Reset the viewer server state")

        .def("add_scene",
             &fvdb::detail::viewer::Viewer::addScene,
             py::arg("scene_name"),
             "Add a new scene to the viewer")

        .def("remove_scene",
             &fvdb::detail::viewer::Viewer::removeScene,
             py::arg("scene_name"),
             "Remove a scene from the viewer")

        .def("remove_view",
             &fvdb::detail::viewer::Viewer::removeView,
             py::arg("scene_name"),
             py::arg("name"),
             "Remove a view from a scene")

        .def("camera_orbit_center",
             &fvdb::detail::viewer::Viewer::cameraOrbitCenter,
             py::arg("scene_name"),
             "Get the point about which the camera orbits")
        .def("set_camera_orbit_center",
             &fvdb::detail::viewer::Viewer::setCameraOrbitCenter,
             py::arg("scene_name"),
             py::arg("x"),
             py::arg("y"),
             py::arg("z"),
             "Set the camera orbit center")

        .def("camera_orbit_radius",
             &fvdb::detail::viewer::Viewer::cameraOrbitRadius,
             py::arg("scene_name"),
             "Get the camera orbit radius")
        .def("set_camera_orbit_radius",
             &fvdb::detail::viewer::Viewer::setCameraOrbitRadius,
             py::arg("scene_name"),
             py::arg("radius"),
             "Set the camera orbit radius (must be positive)")

        .def("camera_up_direction",
             &fvdb::detail::viewer::Viewer::cameraUpDirection,
             py::arg("scene_name"),
             "Get the camera up vector")
        .def("set_camera_up_direction",
             &fvdb::detail::viewer::Viewer::setCameraUpDirection,
             py::arg("scene_name"),
             py::arg("ux"),
             py::arg("uy"),
             py::arg("uz"),
             "Set the camera up vector")

        .def("camera_view_direction",
             &fvdb::detail::viewer::Viewer::cameraViewDirection,
             py::arg("scene_name"),
             "Get the camera view direction")
        .def("set_camera_view_direction",
             &fvdb::detail::viewer::Viewer::setCameraViewDirection,
             py::arg("scene_name"),
             py::arg("dx"),
             py::arg("dy"),
             py::arg("dz"),
             "Set the camera view direction")

        .def("camera_near",
             &fvdb::detail::viewer::Viewer::cameraNear,
             py::arg("scene_name"),
             "Get the camera near clipping plane")
        .def("set_camera_near",
             &fvdb::detail::viewer::Viewer::setCameraNear,
             py::arg("scene_name"),
             py::arg("near"),
             "Set the camera near clipping plane")

        .def("camera_far",
             &fvdb::detail::viewer::Viewer::cameraFar,
             py::arg("scene_name"),
             "Get the camera far clipping plane")
        .def("set_camera_far",
             &fvdb::detail::viewer::Viewer::setCameraFar,
             py::arg("scene_name"),
             py::arg("far"),
             "Set the camera far clipping plane")

        .def("camera_projection_type",
             &fvdb::detail::viewer::Viewer::cameraProjectionType,
             py::arg("scene_name"),
             "The camera mode (perspective or orthographic)")
        .def("set_camera_projection_type",
             &fvdb::detail::viewer::Viewer::setCameraProjectionType,
             py::arg("scene_name"),
             py::arg("mode"),
             "Set the camera mode (perspective or orthographic)")
        .def("add_camera_view",
             py::overload_cast<const std::string &,
                               const std::string &,
                               const torch::Tensor &,
                               const torch::Tensor &,
                               const torch::Tensor &,
                               float,
                               float,
                               float,
                               float,
                               float,
                               float,
                               const std::tuple<float, float, float> &,
                               bool>(&fvdb::detail::viewer::Viewer::addCameraView),
             py::arg("scene_name"),
             py::arg("name"),
             py::arg("camera_to_world_matrices"),
             py::arg("projection_matrices"),
             py::arg("image_sizes"),
             py::arg("frustum_near_plane"),
             py::arg("frustum_far_plane"),
             py::arg("axis_length"),
             py::arg("axis_thickness"),
             py::arg("frustum_line_width"),
             py::arg("frustum_scale"),
             py::arg("frustum_color"),
             py::arg("visible"),
             py::return_value_policy::reference_internal,
             "Add a named camera view from camera/world and projection matrices")
        .def("has_camera_view",
             &fvdb::detail::viewer::Viewer::hasCameraView,
             py::arg("name"),
             "Check if a camera view with the given name exists")
        .def("get_camera_view",
             &fvdb::detail::viewer::Viewer::getCameraView,
             py::arg("name"),
             py::return_value_policy::reference_internal,
             "Get a camera view by name");
}
