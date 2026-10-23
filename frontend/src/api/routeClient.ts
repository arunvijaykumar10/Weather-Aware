import { ApiErrorResponse, RouteAnalyzeRequest, RouteAnalyzeResponse } from '../types/api';

export class ApiError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly details: Record<string, string[] | string | number | undefined>;
  public readonly waitSeconds?: number;

  constructor(
    message: string,
    status: number,
    code: string = 'api_error',
    details: Record<string, string[] | string | number | undefined> = {},
    waitSeconds?: number
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
    this.waitSeconds = waitSeconds;
  }
}

const parseErrorPayload = (responseStatus: number, payload: ApiErrorResponse | null): ApiError => {
  if (payload?.error) {
    const { code, message, details } = payload.error;
    const waitSeconds =
      typeof details?.wait_seconds === 'number' ? details.wait_seconds : undefined;
    return new ApiError(message, responseStatus, code, details || {}, waitSeconds);
  }

  if (responseStatus === 429) {
    return new ApiError(
      'API rate limit exceeded. Please wait a moment before trying again.',
      429,
      'request_throttled'
    );
  }

  return new ApiError(`Request failed with status ${responseStatus}`, responseStatus, 'http_error');
};

export const analyzeRoutes = async (
  requestData: RouteAnalyzeRequest
): Promise<RouteAnalyzeResponse> => {
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const targetUrl = `${apiBaseUrl}/api/routes/analyze/`;

  let response: Response;
  try {
    response = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(requestData),
    });
  } catch (caughtError: unknown) {
    const errorText = caughtError instanceof Error ? caughtError.message : 'Network error';
    throw new ApiError(
      `Cannot connect to backend server at ${apiBaseUrl} (${errorText}). Verify Django is running.`,
      0,
      'network_error'
    );
  }

  if (!response.ok) {
    let errorPayload: ApiErrorResponse | null = null;
    try {
      errorPayload = (await response.json()) as ApiErrorResponse;
    } catch {
      // Non-JSON response (e.g. proxy 502/504 gateway error) handled below.
    }
    throw parseErrorPayload(response.status, errorPayload);
  }

  return (await response.json()) as RouteAnalyzeResponse;
};
