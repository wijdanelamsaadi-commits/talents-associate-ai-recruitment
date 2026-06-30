import { Navigate, Route, Routes } from "react-router-dom";
import { ActivateAccountPage } from "./pages/ActivateAccountPage";
import { AdminProtectedRoute } from "./components/AdminProtectedRoute";
import { AppLayout } from "./components/AppLayout";
import { CandidateProtectedRoute } from "./components/CandidateProtectedRoute";
import { PortalLayout } from "./components/PortalLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { CandidateDetailsPage } from "./pages/CandidateDetailsPage";
import { CandidatesPage } from "./pages/CandidatesPage";
import { CVUploadPage } from "./pages/CVUploadPage";
import { AdminDashboardPage } from "./pages/AdminDashboardPage";
import { AdminSettingsPage } from "./pages/AdminSettingsPage";
import { AdminUsersPage } from "./pages/AdminUsersPage";
import { DashboardPage } from "./pages/DashboardPage";
import { InterviewsPage } from "./pages/InterviewsPage";
import { ImportsPage } from "./pages/ImportsPage";
import { JobOffersPage } from "./pages/JobOffersPage";
import { LoginPage } from "./pages/LoginPage";
import { MatchingPage } from "./pages/MatchingPage";
import { OutlookImportPage } from "./pages/OutlookImportPage";
import { PortalAboutPage } from "./pages/PortalAboutPage";
import { PortalApplyPage } from "./pages/PortalApplyPage";
import { PortalApplicationsPage } from "./pages/PortalApplicationsPage";
import { PortalContactPage } from "./pages/PortalContactPage";
import { PortalHomePage } from "./pages/PortalHomePage";
import { PortalJobDetailsPage } from "./pages/PortalJobDetailsPage";
import { PortalJobsPage } from "./pages/PortalJobsPage";
import { PortalLoginPage } from "./pages/PortalLoginPage";
import { PortalNotificationsPage } from "./pages/PortalNotificationsPage";
import { PortalProfilePage } from "./pages/PortalProfilePage";
import { PortalRegisterPage } from "./pages/PortalRegisterPage";
import { PortalSpontaneousApplicationPage } from "./pages/PortalSpontaneousApplicationPage";
import { PortalStatusPage } from "./pages/PortalStatusPage";

export default function App() {
  return (
    <Routes>
      <Route element={<PortalLayout />}>
        <Route path="/portal" element={<PortalHomePage />} />
        <Route path="/portal/register" element={<PortalRegisterPage />} />
        <Route path="/portal/login" element={<PortalLoginPage />} />
        <Route path="/portal/jobs" element={<PortalJobsPage />} />
        <Route path="/portal/jobs/:jobId" element={<PortalJobDetailsPage />} />
        <Route path="/portal/apply" element={<Navigate to="/portal/jobs" replace />} />
        <Route path="/portal/apply/:jobId" element={<PortalApplyPage />} />
        <Route path="/portal/status" element={<PortalStatusPage />} />
        <Route path="/portal/about" element={<PortalAboutPage />} />
        <Route path="/portal/contact" element={<PortalContactPage />} />
        <Route path="/portal/spontaneous-application" element={<PortalSpontaneousApplicationPage />} />
        <Route element={<CandidateProtectedRoute />}>
          <Route path="/portal/profile" element={<PortalProfilePage />} />
          <Route path="/portal/applications" element={<PortalApplicationsPage />} />
          <Route path="/portal/notifications" element={<PortalNotificationsPage />} />
        </Route>
      </Route>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/activate/:token" element={<ActivateAccountPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/candidates" element={<CandidatesPage />} />
          <Route path="/candidates/:candidateId" element={<CandidateDetailsPage />} />
          <Route path="/cv-upload" element={<CVUploadPage />} />
          <Route path="/imports" element={<ImportsPage />} />
          <Route path="/outlook-import" element={<OutlookImportPage />} />
          <Route path="/jobs" element={<JobOffersPage />} />
          <Route path="/matching" element={<MatchingPage />} />
          <Route path="/interviews" element={<InterviewsPage />} />
          <Route path="/evaluations" element={<Navigate to="/interviews?tab=evaluations" replace />} />
          <Route element={<AdminProtectedRoute />}>
            <Route path="/admin" element={<AdminDashboardPage />} />
            <Route path="/admin/users" element={<AdminUsersPage />} />
            <Route path="/admin/settings" element={<AdminSettingsPage />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  );
}
