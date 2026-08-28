// 백엔드 주소.
//
// 우선순위
//   1. VITE_API_BASE_URL (빌드 시 지정) — 다른 백엔드를 붙일 때 씁니다
//   2. 로컬 개발(localhost)  → 같은 호스트의 4000 포트
//   3. 그 외(배포된 페이지)  → Fly.io 백엔드
//
// 3번 기본값이 없으면 배포본이 존재하지 않는 주소를 부르고, HTTPS
// 페이지에서 HTTP 요청은 브라우저가 차단하므로 변환이 동작하지 않습니다.
// 환경변수를 잊어도 배포본이 살아 있도록 기본값을 코드에 둡니다.
const PROD_API = "https://notaformat.fly.dev";

const _host = window.location.hostname;
const _isLocal = _host === "localhost" || _host === "127.0.0.1";

const SERVER_BASE_URL =
  import.meta.env["VITE_API_BASE_URL"]?.replace(/\/$/, "") ||
  (_isLocal ? `http://${_host}:4000` : PROD_API);

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
