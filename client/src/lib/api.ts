// API Client for LAK Chemicals and Hardware

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

interface ApiOptions extends RequestInit {
  token?: string | null;
}

// Client-side fetch for JSON
export async function apiClient<T>(
  endpoint: string,
  options: ApiOptions = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const { token, ...fetchOptions } = options;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...fetchOptions.headers,
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// Client-side fetch for FormData (file uploads)
export async function apiClientFormData<T>(
  endpoint: string,
  formData: FormData,
  method: string = "POST",
  headersOrOptions: HeadersInit | ApiOptions = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  let headers: HeadersInit = {};
  let token: string | null | undefined;

  // Handle both signatures for backward compatibility or ease of use
  if ('token' in (headersOrOptions as HeadersInit) || !('Content-Type' in (headersOrOptions as HeadersInit))) {
    // Treat as ApiOptions if it has token or doesn't look like pure headers (though RequestInit can satisfy HeadersInit in some cases, clearer to check properties)
    // Actually, let's keep it simple. If it's passed as options object with token:
    const opts = headersOrOptions as ApiOptions;
    token = opts.token;
    if (opts.headers) {
      headers = opts.headers;
    }
  } else {
    headers = headersOrOptions as HeadersInit;
  }

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  // Don't set Content-Type - browser will set it with boundary
  const response = await fetch(url, {
    method,
    body: formData,
    headers,
  },);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}
