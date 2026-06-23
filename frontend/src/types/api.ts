export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
  trace_id: string;
}

export type HttpMethod =
  | "GET"
  | "POST"
  | "PUT"
  | "PATCH"
  | "DELETE"
  | "OPTIONS"
  | "HEAD";

export type RequestData = string | Record<string, unknown> | ArrayBuffer;
