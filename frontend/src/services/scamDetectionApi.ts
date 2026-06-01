const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export type ScamDetectionResult = {
  label: string;
  risk_level: "HIGH" | "MEDIUM" | "LOW" | string;
  risk_score: number;
  scam_type: string;
  explanation: string;
  recommended_action: string;
  triggered_rules: string[];
  model_label?: string | null;
  class_scores: Record<string, number>;
  responsible_ai_note: string;
};

export async function detectScam(text: string): Promise<ScamDetectionResult> {
  const response = await fetch(`${API_BASE_URL}/detect-scam`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Detect scam failed: ${errorText}`);
  }

  return await response.json();
}

export { API_BASE_URL };
