import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/AppLayout";
import { PortalLayout } from "./components/PortalLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { CandidateDetailsPage } from "./pages/CandidateDetailsPage";
import { CandidatesPage } from "./pages/CandidatesPage";
import { CVUploadPage } from "./pages/CVUploadPage";
import { DashboardPage } from "./pages/DashboardPage";
import { EvaluationsPage } from "./pages/EvaluationsPage";
import { InterviewsPage } from "./pages/InterviewsPage";
import { ImportsPage } from "./pages/ImportsPage";
import { JobOffersPage } from "./pages/JobOffersPage";
import { LoginPage } from "./pages/LoginPage";
import { MatchingPage } from "./pages/MatchingPage";
import { OutlookImportPage } from "./pages/OutlookImportPage";
import { PortalApplyPage } from "./pages/PortalApplyPage";
import { PortalHomePage } from "./pages/PortalHomePage";
import { PortalJobDetailsPage } from "./pages/PortalJobDetailsPage";
import { PortalJobsPage } from "./pages/PortalJobsPage";
import { PortalStatusPage } from "./pages/PortalStatusPage";

export default function App() {
  return (
    <Routes>
      <Route element={<PortalLayout />}>
        <Route path="/portal" element={<PortalHomePage />} />
        <Route path="/portal/jobs" element={<PortalJobsPage />} />
        <Route path="/portal/jobs/:jobId" element={<PortalJobDetailsPage />} />
        <Route path="/portal/apply/:jobId" element={<PortalApplyPage />} />
        <Route path="/portal/status" element={<PortalStatusPage />} />
      </Route>
      <Route path="/login" element={<LoginPage />} />
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
          <Route path="/evaluations" element={<EvaluationsPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
