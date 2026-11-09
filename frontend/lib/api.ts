export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Unit = { unit: string; normalized_unit: string; token: string };
export type Encoding = {
  raw_text: string; normalized_text: string; profile_id: string; profile_version: number;
  removed_units: string[]; units: Unit[]; encoded_pattern: string; pattern_length: number;
};
export type Corpus = { constant: string; version: string; digits: number; position_basis: string; sha256: string; source: string };
export type SearchResponse = {
  query: Encoding;
  corpus: { constant: string; version: string; digits_searched: number; position_basis: string };
  result: { found: boolean; first_position: number | null; matches: number[]; total_matches: number | null; count_complete: boolean; positions_complete: boolean; next_cursor: string | null };
  execution: { method: string; complete: boolean; elapsed_ms: number };
};

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, { ...options, headers: { "Content-Type": "application/json", ...options?.headers } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : `Request failed (${response.status})`);
  return data as T;
}

export function post<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: "POST", body: JSON.stringify(body) });
}

export const number = (value: number) => value.toLocaleString("en-US");
