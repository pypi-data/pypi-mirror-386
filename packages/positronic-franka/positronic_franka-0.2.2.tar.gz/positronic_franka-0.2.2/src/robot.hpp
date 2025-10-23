#pragma once

#include <franka/robot.h>
#include <franka/control_types.h>
#include <franka/model.h>
#include <franka/robot_state.h>

#include <array>
#include <cmath>
#include <algorithm>
#include <iostream>
#include <string>
#include <thread>
#include <atomic>
#include <mutex>
#include <condition_variable>
#include <cstring>
#include <Eigen/Core>
#include <Eigen/Geometry>
#include <ruckig/ruckig.hpp>
#include <ruckig/input_parameter.hpp>
#include <osqp.h>
#include <stdexcept>

namespace positronic_franka {

// Panda joint limits (rad/s, rad/s^2, rad/s^3)
constexpr std::array<double, 7> PANDA_BASE_VELOCITY_LIMITS = {2.62, 2.62, 2.62, 2.62, 5.26, 4.18, 5.26};
constexpr std::array<double, 7> PANDA_BASE_ACCELERATION_LIMITS = {10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0};
constexpr std::array<double, 7> PANDA_BASE_JERK_LIMITS = {5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0};
constexpr std::array<double, 7> PANDA_JOINT_LOWER_LIMITS = {
    -2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973};
constexpr std::array<double, 7> PANDA_JOINT_UPPER_LIMITS = {
    2.8973, 1.7628, 2.8973, 3.0718, 2.8973, 3.7525, 2.8973};

// Common Eigen aliases
using Vector7d = Eigen::Matrix<double, 7, 1>;
using Vector6d = Eigen::Matrix<double, 6, 1>;
using SpatialJacobian = Eigen::Matrix<double, 6, 7>;

struct State {
  Vector7d q;
  Vector7d dq;
  // End-effector pose in base (robot) frame: [tx, ty, tz, qw, qx, qy, qz]
  Vector7d end_effector_pose;
  int error = 0;
  // External wrench (force, torque) on end-effector frame expressed in K frame.
  Vector6d end_effector_wrench = Vector6d::Zero();
};

class Robot {
 public:
  explicit Robot(const std::string& ip,
                 franka::RealtimeConfig realtime_config = franka::RealtimeConfig::kIgnore,
                 double relative_dynamics_factor = 1.0)
      : ip_(ip),
        robot_(std::make_unique<franka::Robot>(ip, realtime_config)),
        relative_dynamics_factor_(std::clamp(relative_dynamics_factor, 0.0001, 1.0)) {
    model_ = std::make_unique<franka::Model>(robot_->loadModel());
  }

  ~Robot() {
    stop_control_loop_();
  }

  State state() {
    franka::RobotState rs = read_robot_state_();
    // Map the column-major 4x4 transform into Eigen
    Eigen::Map<const Eigen::Matrix4d> T(rs.O_T_EE.data());
    const Eigen::Vector3d t = T.block<3, 1>(0, 3);
    const Eigen::Matrix3d R = T.block<3, 3>(0, 0);
    const Eigen::Quaterniond q(R);

    State st{};
    st.q = Eigen::Map<const Vector7d>(rs.q.data());
    st.dq = Eigen::Map<const Vector7d>(rs.dq.data());
    st.end_effector_pose << t.x(), t.y(), t.z(), q.w(), q.x(), q.y(), q.z();
    st.error = rs.current_errors ? 1 : 0;
    // NOTE: This relies on the fact that we don't configure EE_T_K frame.
    st.end_effector_wrench = Eigen::Map<const Vector6d>(rs.K_F_ext_hat_K.data());
    return st;
  }

  void set_target_joints(const Eigen::Ref<const Vector7d>& q_target,
                         bool asynchronous = true) {
    if (!control_running_.load()) {
      if (control_thread_.joinable()) {
        control_thread_.join();
      }
      stop_requested_.store(false);
      control_running_.store(true);
      control_thread_ = std::thread([this] { this->run_joint_position_control_(); });
    }
    if (!asynchronous) {
      // Prepare synchronous wait before publishing the target to avoid races.
      std::lock_guard<std::mutex> glk(goal_mutex_);
      goal_completed_ = false;
      sync_request_next_.store(true);
    }
    {
      std::lock_guard<std::mutex> lk(target_mutex_);
      target_q_ = q_target;
      has_target_.store(true);
    }
    if (!asynchronous) {
      std::unique_lock<std::mutex> lk(goal_mutex_);
      goal_cv_.wait(lk, [&]{ return goal_completed_; });
    }
  }

  // Forward Kinematics: compute EE pose (tx, ty, tz, qw, qx, qy, qz) from joints q (7,)
  Vector7d forward_kinematics(
      const Eigen::Ref<const Vector7d>& q) {
    // Use current robot state for fixed frames (F_T_EE, EE_T_K), override q
    franka::RobotState st = read_robot_state_();
    st.q = to_std_array7_(q);

    const Eigen::Matrix4d T = ee_pose_matrix_(st);
    const Eigen::Vector3d t = T.block<3, 1>(0, 3);
    const Eigen::Matrix3d R = T.block<3, 3>(0, 0);
    const Eigen::Quaterniond quat(R);

    Vector7d pose;
    pose << t.x(), t.y(), t.z(), quat.w(), quat.x(), quat.y(), quat.z();
    return pose;
  }

  // Inverse Kinematics to EndEffector pose in base frame (tx, ty, tz, qw, qx, qy, qz)
  Vector7d inverse_kinematics(
      const Eigen::Ref<const Vector7d>& target_pose_wxyz,
      double tol = 1e-4, int max_iters = 150, double min_step = 1e-8, double pinv_reg = 0.03,
      double nullspace_gain = 0.002, double line_search_alpha = 1.0, double line_search_beta = 0.5,
      int line_search_max_steps = 20) {
    auto base = read_robot_state_();
    Vector7d q0 = Eigen::Map<const Vector7d>(base.q.data());
    return inverse_kinematics_q0(target_pose_wxyz, q0, tol, max_iters, min_step, pinv_reg, nullspace_gain,
                                 line_search_alpha, line_search_beta, line_search_max_steps);
  }

  Vector7d inverse_kinematics_q0(
      const Eigen::Ref<const Vector7d>& target_pose_wxyz,
      const Eigen::Ref<const Vector7d>& q0,
      double tol = 1e-4, int max_iters = 150, double min_step = 1e-8, double pinv_reg = 0.03,
      double nullspace_gain = 0.002, double line_search_alpha = 1.0, double line_search_beta = 0.5,
      int line_search_max_steps = 20) {
    // Target
    const Eigen::Vector3d t_tgt = target_pose_wxyz.head<3>();
    Eigen::Quaterniond q_tgt(target_pose_wxyz(3), target_pose_wxyz(4), target_pose_wxyz(5), target_pose_wxyz(6));
    q_tgt.normalize();
    const Eigen::Matrix3d R_tgt = q_tgt.toRotationMatrix();

    // Base state for frames (F_T_EE, EE_T_K). We'll vary q only.
    franka::RobotState base = read_robot_state_();
    franka::RobotState st = base;
    Vector7d q = q0;

    for (int it = 0; it < max_iters; ++it) {
      // Update state with current q
      st.q = to_std_array7_(q);

      // Pose and error
      const Eigen::Matrix4d T_cur = ee_pose_matrix_(st);
      const Eigen::Matrix<double, 6, 1> e = cartesian_error_(T_cur, t_tgt, R_tgt);
      const double err_norm = e.norm();
      if (err_norm < tol) break;

      // Jacobian and DLS step with nullspace bias
      const SpatialJacobian J = ee_jacobian_(st);
      const Eigen::Matrix<double, 7, 6> J_pinv = damped_pinv_(J, pinv_reg);
      const Vector7d dq_primary = -J_pinv * e;
      const Eigen::Matrix<double, 7, 7> N = Eigen::Matrix<double, 7, 7>::Identity() - J_pinv * J;
      const Vector7d dq_null = N * (-nullspace_gain * std::exp(err_norm) * q);
      const Vector7d dq = dq_primary + dq_null;

      // Backtracking line search on error norm with improvement check
      double step = line_search_alpha;
      double best_err = err_norm;
      for (int ls = 0; ls < line_search_max_steps; ++ls) {
        const Vector7d q_trial = q + step * dq;
        st.q = to_std_array7_(q_trial);
        const Eigen::Matrix4d T_trial = ee_pose_matrix_(st);
        const double err_trial = cartesian_error_(T_trial, t_tgt, R_tgt).norm();
        if (err_trial < best_err) {
          best_err = err_trial;
          q = q_trial;
        }
        step *= line_search_beta;
        if (step < min_step) break;  // Stop searching further if step is too small
      }
      if (best_err >= err_norm - 1e-9) break;  // No meaningful improvement, terminate
    }
    // Print final Cartesian error (translation in mm, rotation in degrees) to stderr
    st.q = to_std_array7_(q);
    const Eigen::Matrix4d T_final = ee_pose_matrix_(st);
    const Eigen::Matrix<double, 6, 1> e_final = cartesian_error_(T_final, t_tgt, R_tgt);
    const double trans_err_mm = 1000.0 * e_final.head<3>().norm();
    const double rot_err_deg = (180.0 / M_PI) * e_final.tail<3>().norm();
    return q;
  }

  Vector7d inverse_kinematics_with_limits(
      const Eigen::Ref<const Vector7d>& target_pose_wxyz,
      double tol = 1e-4, int max_iters = 150, double min_step = 1e-8, double pinv_reg = 0.03,
      double nullspace_gain = 0.002, double line_search_alpha = 1.0, double line_search_beta = 0.5,
      int line_search_max_steps = 20) {
    auto base = read_robot_state_();
    Vector7d q0 = Eigen::Map<const Vector7d>(base.q.data());
    return inverse_kinematics_with_limits(target_pose_wxyz, q0, tol, max_iters, min_step, pinv_reg,
                                          nullspace_gain, line_search_alpha, line_search_beta,
                                          line_search_max_steps);
  }

  Vector7d inverse_kinematics_with_limits(
      const Eigen::Ref<const Vector7d>& target_pose_wxyz,
      const Eigen::Ref<const Vector7d>& q0,
      double tol = 1e-4, int max_iters = 150, double min_step = 1e-8, double pinv_reg = 0.03,
      double nullspace_gain = 0.002, double line_search_alpha = 1.0, double line_search_beta = 0.5,
      int line_search_max_steps = 20) {
    static_cast<void>(line_search_beta);
    static_cast<void>(line_search_max_steps);

    const Eigen::Vector3d t_tgt = target_pose_wxyz.head<3>();
    Eigen::Quaterniond q_tgt(target_pose_wxyz(3), target_pose_wxyz(4), target_pose_wxyz(5),
                             target_pose_wxyz(6));
    q_tgt.normalize();
    const Eigen::Matrix3d R_tgt = q_tgt.toRotationMatrix();

    franka::RobotState base = read_robot_state_();
    franka::RobotState st = base;
    Vector7d q = q0;

    const double regularization = std::max(pinv_reg, 1e-6);

    const c_int n = 7;
    const c_int m = 7;
    std::vector<c_int> A_indptr(n + 1, 0);
    std::vector<c_int> A_indices;
    std::vector<c_float> A_data;
    A_indices.reserve(n);
    A_data.reserve(n);
    for (c_int col = 0; col < n; ++col) {
      A_indptr[col] = static_cast<c_int>(A_data.size());
      A_indices.push_back(col);
      A_data.push_back(1.0);
    }
    A_indptr[n] = static_cast<c_int>(A_data.size());

    OSQPSettings settings;
    osqp_set_default_settings(&settings);
    settings.verbose = 0;
    settings.polish = 0;
    settings.max_iter = 400;
    settings.eps_abs = std::min(1e-6, tol * 0.1);
    settings.eps_rel = std::min(1e-6, tol * 0.1);
    settings.warm_start = 0;

    for (int it = 0; it < max_iters; ++it) {
      st.q = to_std_array7_(q);
      const Eigen::Matrix4d T_cur = ee_pose_matrix_(st);
      const Eigen::Matrix<double, 6, 1> e = cartesian_error_(T_cur, t_tgt, R_tgt);
      const double err_norm = e.norm();
      if (err_norm < tol)
        break;

      const SpatialJacobian J = ee_jacobian_(st);
      const Eigen::Matrix<double, 7, 7> P = J.transpose() * J +
                                            regularization * Eigen::Matrix<double, 7, 7>::Identity();

      std::vector<c_int> P_indptr(n + 1, 0);
      std::vector<c_int> P_indices;
      std::vector<c_float> P_data;
      P_indices.reserve(n * (n + 1) / 2);
      P_data.reserve(n * (n + 1) / 2);
      for (c_int col = 0; col < n; ++col) {
        P_indptr[col] = static_cast<c_int>(P_data.size());
        for (c_int row = 0; row <= col; ++row) {
          const double value = P(row, col);
          if (std::abs(value) < 1e-12)
            continue;
          P_indices.push_back(row);
          P_data.push_back(static_cast<c_float>(value));
        }
      }
      P_indptr[n] = static_cast<c_int>(P_data.size());

      c_float* A_data_raw = static_cast<c_float*>(c_malloc(A_data.size() * sizeof(c_float)));
      c_int* A_indices_raw = static_cast<c_int*>(c_malloc(A_indices.size() * sizeof(c_int)));
      c_int* A_indptr_raw = static_cast<c_int*>(c_malloc(A_indptr.size() * sizeof(c_int)));
      if (!A_data_raw || !A_indices_raw || !A_indptr_raw) {
        if (A_data_raw) c_free(A_data_raw);
        if (A_indices_raw) c_free(A_indices_raw);
        if (A_indptr_raw) c_free(A_indptr_raw);
        throw std::runtime_error("Failed to allocate OSQP constraint buffers.");
      }
      std::memcpy(A_data_raw, A_data.data(), A_data.size() * sizeof(c_float));
      std::memcpy(A_indices_raw, A_indices.data(), A_indices.size() * sizeof(c_int));
      std::memcpy(A_indptr_raw, A_indptr.data(), A_indptr.size() * sizeof(c_int));
      csc* A_csc = csc_matrix(m, n, static_cast<c_int>(A_data.size()), A_data_raw, A_indices_raw,
                              A_indptr_raw);
      if (!A_csc) {
        c_free(A_data_raw);
        c_free(A_indices_raw);
        c_free(A_indptr_raw);
        throw std::runtime_error("Failed to construct OSQP constraint matrix.");
      }

      c_float* P_data_raw = static_cast<c_float*>(c_malloc(P_data.size() * sizeof(c_float)));
      c_int* P_indices_raw = static_cast<c_int*>(c_malloc(P_indices.size() * sizeof(c_int)));
      c_int* P_indptr_raw = static_cast<c_int*>(c_malloc(P_indptr.size() * sizeof(c_int)));
      if (!P_data_raw || !P_indices_raw || !P_indptr_raw) {
        if (P_data_raw) c_free(P_data_raw);
        if (P_indices_raw) c_free(P_indices_raw);
        if (P_indptr_raw) c_free(P_indptr_raw);
        csc_spfree(A_csc);
        throw std::runtime_error("Failed to allocate OSQP Hessian buffers.");
      }
      std::memcpy(P_data_raw, P_data.data(), P_data.size() * sizeof(c_float));
      std::memcpy(P_indices_raw, P_indices.data(), P_indices.size() * sizeof(c_int));
      std::memcpy(P_indptr_raw, P_indptr.data(), P_indptr.size() * sizeof(c_int));

      csc* P_csc = csc_matrix(n, n, static_cast<c_int>(P_data.size()), P_data_raw, P_indices_raw,
                              P_indptr_raw);
      if (!P_csc) {
        c_free(P_data_raw);
        c_free(P_indices_raw);
        c_free(P_indptr_raw);
        csc_spfree(A_csc);
        throw std::runtime_error("Failed to construct OSQP Hessian matrix.");
      }

      std::vector<c_float> q_vec(n, 0.0);
      Vector7d grad = J.transpose() * e;
      for (c_int i = 0; i < n; ++i) {
        q_vec[static_cast<size_t>(i)] =
            static_cast<c_float>(grad(static_cast<Eigen::Index>(i)));
      }

      std::vector<c_float> lower(m, 0.0);
      std::vector<c_float> upper(m, 0.0);
      for (c_int i = 0; i < m; ++i) {
        const double min_bound = PANDA_JOINT_LOWER_LIMITS[static_cast<size_t>(i)] -
                                 q(static_cast<Eigen::Index>(i));
        const double max_bound = PANDA_JOINT_UPPER_LIMITS[static_cast<size_t>(i)] -
                                 q(static_cast<Eigen::Index>(i));
        lower[static_cast<size_t>(i)] = static_cast<c_float>(min_bound);
        upper[static_cast<size_t>(i)] = static_cast<c_float>(max_bound);
      }

      c_float* q_raw = static_cast<c_float*>(c_malloc(n * sizeof(c_float)));
      c_float* l_raw = static_cast<c_float*>(c_malloc(m * sizeof(c_float)));
      c_float* u_raw = static_cast<c_float*>(c_malloc(m * sizeof(c_float)));
      if (!q_raw || !l_raw || !u_raw) {
        if (q_raw) c_free(q_raw);
        if (l_raw) c_free(l_raw);
        if (u_raw) c_free(u_raw);
        csc_spfree(P_csc);
        csc_spfree(A_csc);
        throw std::runtime_error("Failed to allocate OSQP vector buffers.");
      }
      for (c_int i = 0; i < n; ++i)
        q_raw[i] = q_vec[static_cast<size_t>(i)];
      for (c_int i = 0; i < m; ++i) {
        l_raw[i] = lower[static_cast<size_t>(i)];
        u_raw[i] = upper[static_cast<size_t>(i)];
      }

      OSQPData data;
      data.n = n;
      data.m = m;
      data.P = P_csc;
      data.A = A_csc;
      data.q = q_raw;
      data.l = l_raw;
      data.u = u_raw;

      OSQPWorkspace* workspace = nullptr;
      const c_int setup_status = osqp_setup(&workspace, &data, &settings);
      if (setup_status != 0 || workspace == nullptr) {
        if (workspace) osqp_cleanup(workspace);
        c_free(q_raw);
        c_free(l_raw);
        c_free(u_raw);
        csc_spfree(P_csc);
        csc_spfree(A_csc);
        throw std::runtime_error("Failed to set up OSQP solver.");
      }

      const c_int solve_status = osqp_solve(workspace);
      if (solve_status != 0 || workspace->info == nullptr ||
          (workspace->info->status_val != OSQP_SOLVED &&
           workspace->info->status_val != OSQP_SOLVED_INACCURATE)) {
        osqp_cleanup(workspace);
        c_free(q_raw);
        c_free(l_raw);
        c_free(u_raw);
        csc_spfree(P_csc);
        csc_spfree(A_csc);
        break;
      }

      Vector7d dq = Vector7d::Zero();
      for (c_int i = 0; i < n; ++i)
        dq(static_cast<Eigen::Index>(i)) =
            static_cast<double>(workspace->solution->x[static_cast<size_t>(i)]);

      osqp_cleanup(workspace);
      c_free(q_raw);
      c_free(l_raw);
      c_free(u_raw);
      csc_spfree(P_csc);
      csc_spfree(A_csc);

      if (dq.norm() < min_step)
        break;

      double step_scale = 1.0;
      if (line_search_alpha > 0.0 && dq.norm() > line_search_alpha)
        step_scale = line_search_alpha / dq.norm();

      Vector7d q_next = q + step_scale * dq;
      for (size_t i = 0; i < 7; ++i) {
        const double lower_limit = PANDA_JOINT_LOWER_LIMITS[i];
        const double upper_limit = PANDA_JOINT_UPPER_LIMITS[i];
        q_next(static_cast<Eigen::Index>(i)) =
            std::clamp(q_next(static_cast<Eigen::Index>(i)), lower_limit, upper_limit);
      }

      if ((q_next - q).norm() < min_step)
        break;
      q = q_next;
    }

    st.q = to_std_array7_(q);
    const Eigen::Matrix4d T_final = ee_pose_matrix_(st);
    const Eigen::Matrix<double, 6, 1> e_final = cartesian_error_(T_final, t_tgt, R_tgt);
    const double trans_err_mm = 1000.0 * e_final.head<3>().norm();
    const double rot_err_deg = (180.0 / M_PI) * e_final.tail<3>().norm();
    static_cast<void>(trans_err_mm);
    static_cast<void>(rot_err_deg);
    return q;
  }

private:

  // Utilities for IK readability
  static std::array<double, 7> to_std_array7_(const Vector7d& v) {
    std::array<double, 7> a{};
    for (size_t i = 0; i < 7; ++i) a[i] = v(i);
    return a;
  }

  Eigen::Matrix4d ee_pose_matrix_(const franka::RobotState& st) const {
    const auto T_data = model_->pose(franka::Frame::kEndEffector, st);
    return Eigen::Map<const Eigen::Matrix4d>(T_data.data());
  }

  SpatialJacobian ee_jacobian_(const franka::RobotState& st) const {
    const auto J_data = model_->zeroJacobian(franka::Frame::kEndEffector, st);
    return Eigen::Map<const SpatialJacobian>(J_data.data());
  }

  static Eigen::Matrix<double, 6, 1> cartesian_error_(const Eigen::Matrix4d& T_cur,
                                                      const Eigen::Vector3d& t_tgt,
                                                      const Eigen::Matrix3d& R_tgt) {
    const Eigen::Vector3d t_cur = T_cur.block<3, 1>(0, 3);
    const Eigen::Matrix3d R_cur = T_cur.block<3, 3>(0, 0);
    const Eigen::Vector3d e_pos = t_cur - t_tgt;
    const Eigen::Matrix3d R_rel = R_cur.transpose() * R_tgt;
    const Eigen::AngleAxisd aa(R_rel);
    const Eigen::Vector3d w = aa.angle() * aa.axis();
    const Eigen::Vector3d e_rot = -R_cur * w;
    Eigen::Matrix<double, 6, 1> e;
    e << e_pos, e_rot;
    return e;
  }

  static Eigen::Matrix<double, 7, 6> damped_pinv_(const SpatialJacobian& J, double lambda) {
    const Eigen::Matrix<double, 6, 6> JJt = J * J.transpose();
    const Eigen::Matrix<double, 6, 6> A = JJt + lambda * Eigen::Matrix<double, 6, 6>::Identity();
    return J.transpose() * A.inverse();
  }

 public:
  double relative_dynamics_factor() const { return relative_dynamics_factor_; }

 private:
  void run_joint_position_control_() {
    try {
      // Initialize Ruckig OTG
      constexpr double control_rate_hz = 1000.0;
      ruckig::Ruckig<7> otg(1.0 / control_rate_hz);
      ruckig::InputParameter<7> ip;
      ruckig::OutputParameter<7> op;

      {
        std::lock_guard<std::mutex> lk(target_mutex_);
        for (size_t i = 0; i < 7; ++i) ip.target_position[i] = target_q_[i];
        ip.target_velocity.fill(0.0);
        ip.target_acceleration.fill(0.0);
      }
      // Encourage smooth, time-synchronized motion
      ip.synchronization = ruckig::Synchronization::Time;

      // Apply scaled limits once; they remain constant for this motion
      for (size_t i = 0; i < 7; ++i) {
        ip.max_velocity[i] = PANDA_BASE_VELOCITY_LIMITS[i] * relative_dynamics_factor_;
        ip.max_acceleration[i] = PANDA_BASE_ACCELERATION_LIMITS[i] * relative_dynamics_factor_;
        ip.max_jerk[i] = PANDA_BASE_JERK_LIMITS[i] * relative_dynamics_factor_;
      }

      robot_->control(
        [&, this,
         first = true,
         sync_in_flight = false,
         stopping = false,
         result = ruckig::Result::Finished](const franka::RobotState& st, franka::Duration /*period*/) mutable -> franka::JointPositions {
          {
            std::lock_guard<std::mutex> lk(last_state_mutex_);
            last_state_ = std::make_unique<franka::RobotState>(st);
          }
          if (first) {
            for (size_t i = 0; i < 7; ++i) {
              ip.current_position[i] = st.q[i];
              ip.current_velocity[i] = st.dq[i];
              ip.current_acceleration[i] = 0.0;
              ip.target_position[i] = st.q[i];
              ip.target_velocity[i] = 0.0;
            }
            // It is important to set the result to Working here, so that if robot is in motion, we will safely stop it
            result = ruckig::Result::Working;
            first = false;
          } else if (!stopping && stop_requested_.load()) {
            stopping = true;
            has_target_.store(false);
            for (size_t i = 0; i < 7; ++i) {
              ip.target_position[i] = ip.current_position[i];
              ip.target_velocity[i] = 0.0;
              ip.target_acceleration[i] = 0.0;
            }
            result = ruckig::Result::Working;
          }

          if (!stopping && has_target_.load()) {  // Update target if changed
            std::lock_guard<std::mutex> lk(target_mutex_);
            for (size_t i = 0; i < 7; ++i) {
              ip.target_position[i] = target_q_[i];
            }
            result = ruckig::Result::Working;
            has_target_.store(false);
            sync_in_flight = sync_request_next_.exchange(false);
          }

          if (result == ruckig::Result::Working) {
            result = otg.update(ip, op);
            op.pass_to_input(ip);
            return franka::JointPositions(op.new_position);;
          }
          if (sync_in_flight) {
            {
              std::lock_guard<std::mutex> lk(goal_mutex_);
              goal_completed_ = true;
            }
            goal_cv_.notify_all();
            sync_in_flight = false;
          }
          auto cmd = franka::JointPositions(op.new_position);
          if (stopping)
            cmd.motion_finished = true;
          return cmd;
        });
    } catch (const std::exception& e) {
      std::cerr << "Joint control thread error: " << e.what() << std::endl;
    }
    control_running_.store(false);
  }

 public:
  void set_joint_impedance(const std::array<double, 7>& joint_stiffness) {
    robot_->setJointImpedance(joint_stiffness);
  }

  void set_cartesian_impedance(const std::array<double, 6>& cartesian_stiffness) {
    robot_->setCartesianImpedance(cartesian_stiffness);
  }

  void set_collision_behavior(
      const std::array<double, 7>& lower_torque_thresholds_acceleration,
      const std::array<double, 7>& upper_torque_thresholds_acceleration,
      const std::array<double, 7>& lower_torque_thresholds_nominal,
      const std::array<double, 7>& upper_torque_thresholds_nominal,
      const std::array<double, 6>& lower_force_thresholds_acceleration,
      const std::array<double, 6>& upper_force_thresholds_acceleration,
      const std::array<double, 6>& lower_force_thresholds_nominal,
      const std::array<double, 6>& upper_force_thresholds_nominal) {
    robot_->setCollisionBehavior(
        lower_torque_thresholds_acceleration,
        upper_torque_thresholds_acceleration,
        lower_torque_thresholds_nominal,
        upper_torque_thresholds_nominal,
        lower_force_thresholds_acceleration,
        upper_force_thresholds_acceleration,
        lower_force_thresholds_nominal,
        upper_force_thresholds_nominal);
  }

  void set_load(double mass,
                const std::array<double, 3>& F_x_Cload,
                const std::array<double, 9>& I_x_Cload) {
    robot_->setLoad(mass, F_x_Cload, I_x_Cload);
  }

  bool recover_from_errors() {
    stop_control_loop_();
    stop_requested_.store(false);
    robot_->automaticErrorRecovery();
    auto state = read_robot_state_();
    return !static_cast<bool>(state.current_errors);
  }

 private:
  franka::RobotState read_robot_state_() {
    if (control_running_.load()) {
      std::lock_guard<std::mutex> lk(last_state_mutex_);
      if (last_state_ != nullptr)
        return *last_state_;
    }
    return robot_->readOnce();
  }

  std::string ip_;
  std::unique_ptr<franka::Robot> robot_;
  std::unique_ptr<franka::Model> model_;
  std::thread control_thread_;
  std::atomic<bool> control_running_{false};
  std::atomic<bool> stop_requested_{false};
  std::atomic<bool> has_target_{false};

  // Synchronization for synchronous set_target_joints
  std::mutex goal_mutex_;
  std::condition_variable goal_cv_;
  bool goal_completed_ = false;
  std::atomic<bool> sync_request_next_{false};

  std::mutex last_state_mutex_;
  std::unique_ptr<franka::RobotState> last_state_;

  const double relative_dynamics_factor_{1.0};
  std::mutex target_mutex_;
  Vector7d target_q_ = Vector7d::Zero();

  void stop_control_loop_() {
    stop_requested_.store(true);
    if (control_thread_.joinable()) {
      control_thread_.join();
    }
    control_running_.store(false);
    has_target_.store(false);
    {
      std::lock_guard<std::mutex> lk(goal_mutex_);
      goal_completed_ = true;
    }
    goal_cv_.notify_all();
    stop_requested_.store(false);
  }
};

}  // namespace positronic_franka
