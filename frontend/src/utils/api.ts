export const apiFetch = async (input: RequestInfo, init?: RequestInit) => {
  const requestInput = typeof input === 'string' && input.startsWith('/')
    ? `/api${input}`
    : input;

  const response = await fetch(requestInput, {
    ...init,
    credentials: 'include', // Important for sending cookies (httpOnly) with requests
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  const contentType = response.headers.get('content-type') ?? '';
  const isJson = contentType.includes('application/json');

  // Never try to parse the SPA HTML as JSON. Keep the endpoint in the error so
  // a proxy/configuration regression is immediately visible in the UI.
  if (!response.ok) {
    const errorData = isJson ? await response.json().catch(() => ({})) : {};
    throw new Error(
      errorData.detail ?? errorData.message ?? `API request ${String(requestInput)} failed: HTTP ${response.status}`
    );
  }

  // If there's no content, return null
  if (response.status === 204) {
    return null;
  }

  if (!isJson) {
    throw new Error(`API request ${String(requestInput)} returned ${contentType || 'an unknown content type'} instead of JSON`);
  }

  return response.json();
};

// Helper function to build URL with query parameters
export const buildUrlWithQuery = (baseUrl: string, params: Record<string, string | number | boolean | undefined>) => {
  const url = new URL(baseUrl, window.location.origin);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.append(key, String(value));
    }
  });
  return url.toString();
};
