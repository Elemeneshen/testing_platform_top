let sessionRedirectInProgress = false;

const apiErrorMessage = (errorData: any, requestInput: RequestInfo, status: number) => {
  if (typeof errorData?.detail === 'string') return errorData.detail;
  if (typeof errorData?.message === 'string') return errorData.message;
  if (Array.isArray(errorData?.detail)) {
    return errorData.detail.map((item: any) => item?.msg ?? String(item)).join('; ');
  }
  return `API request ${String(requestInput)} failed: HTTP ${status}`;
};

const redirectToLogin = () => {
  if (sessionRedirectInProgress) return;
  const path = window.location.pathname;
  const isLoginPage = path === '/login' || path === '/teacher/login' || path === '/register';
  if (isLoginPage) return;

  sessionRedirectInProgress = true;
  const teacherArea = path.startsWith('/teacher');
  localStorage.removeItem('codeclass-auth');
  window.location.replace(teacherArea ? '/teacher/login' : '/login');
};

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

  if (response.status === 401) {
    redirectToLogin();
  }

  // Never try to parse the SPA HTML as JSON. Keep the endpoint in the error so
  // a proxy/configuration regression is immediately visible in the UI.
  if (!response.ok) {
    const errorData = isJson ? await response.json().catch(() => ({})) : {};
    throw new Error(apiErrorMessage(errorData, requestInput, response.status));
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
