export const apiFetch = async (input: RequestInfo, init?: RequestInit) => {
  const response = await fetch(input, {
    ...init,
    credentials: 'include', // Important for sending cookies (httpOnly) with requests
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  // If the response is not OK, we can throw an error with the status and message
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail ?? errorData.message ?? `HTTP error! status: ${response.status}`
    );
  }

  // If there's no content, return null
  if (response.status === 204) {
    return null;
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
