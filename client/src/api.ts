const SERVER_BASE_URL = `http://${window.location.hostname}:4000`;

export { SERVER_BASE_URL };

export async function apiFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = localStorage.getItem("access_token");

  const headers: Record<string, string> = {};

  // Content-Type은 FormData일 때 자동 설정되므로 수동 설정하지 않음
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // 기존 헤더와 병합
  const existingHeaders = options.headers as Record<string, string> | undefined;
  if (existingHeaders) {
    Object.assign(headers, existingHeaders);
  }

  let res = await fetch(`${SERVER_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  // 401이면 refresh token으로 재시도
  if (res.status === 401 && token) {
    const refreshToken = localStorage.getItem("refresh_token");
    if (refreshToken) {
      const refreshRes = await fetch(`${SERVER_BASE_URL}/api/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (refreshRes.ok) {
        const data = await refreshRes.json();
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);

        headers["Authorization"] = `Bearer ${data.access_token}`;
        res = await fetch(`${SERVER_BASE_URL}${path}`, {
          ...options,
          headers,
        });
      } else {
        // refresh도 실패 → 로그아웃
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      }
    }
  }

  return res;
}

export async function apiGet(path: string): Promise<Response> {
  return apiFetch(path, { method: "GET" });
}

export async function apiPost(
  path: string,
  body?: unknown
): Promise<Response> {
  return apiFetch(path, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export async function apiPut(
  path: string,
  body?: unknown
): Promise<Response> {
  return apiFetch(path, {
    method: "PUT",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export async function apiPostFormData(
  path: string,
  formData: FormData
): Promise<Response> {
  return apiFetch(path, {
    method: "POST",
    body: formData,
  });
}
