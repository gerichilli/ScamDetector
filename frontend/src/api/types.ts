export type User = {
  id: string;
  email: string | null;
  phone_number: string | null;
  full_name: string | null;
  role: "user" | "moderator" | "admin";
  status: string;
};

export type TrustedContact = {
  id: string;
  full_name: string;
  email: string;
  phone_number: string | null;
  status: "pending" | "confirmed";
  confirmed_at: string | null;
  created_at: string;
  confirmation_preview_url: string | null;
};

export type LookupResponse = {
  found: boolean;
  message?: string;
  entity?: {
    id: string;
    entity_type: string;
    value: string;
    risk_level: RiskLevel;
    status: string;
    report_count: number;
    verified_report_count: number;
    first_reported_at: string | null;
    last_reported_at: string | null;
  };
  summary?: {
    top_scam_types: Array<{ scam_type: string; count: number }>;
  };
};

export type RiskLevel = "low" | "medium" | "high" | "critical";

export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type ReportListItem = {
  id: string;
  entity_type: string;
  entity_value: string;
  scam_type: string;
  status: string;
  created_at: string;
};

export type HistoryItem = {
  id: string;
  query_type: string;
  query_value: string;
  result_found: boolean;
  result_risk_level: RiskLevel | null;
  created_at: string;
};

export type AlertHistoryItem = {
  call_id: string;
  alert_id: string;
  phone_number: string;
  risk_level: RiskLevel;
  message: string;
  recommended_action: string;
  call_time: string;
  duration_seconds: number | null;
};

export type CallAlertResponse = {
  call_id: string;
  alert_id: string;
  phone_number: string;
  risk_level: RiskLevel;
  message: string;
  recommended_action: string;
  call_time: string;
};

export type CallReportItem = {
  call_id: string;
  alert_id: string;
  phone_number: string;
  risk_level: RiskLevel;
  call_time: string;
  duration_seconds: number | null;
  transcript: string | null;
  note: string | null;
  message: string;
  recommended_action: string;
  status: string;
};
