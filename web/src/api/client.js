const BASE = "/api/v1";

let accessToken = null;

export function setAccessToken(value) {
  accessToken = value || null;
}

export class ApiError extends Error {
  constructor(message, status = 0, code = "internal_error", details = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function errorFromPayload(payload, status) {
  if (payload && payload.error) {
    return new ApiError(
      payload.error.message || "La requête a échoué.",
      status,
      payload.error.code || "internal_error",
      payload.error.details || {}
    );
  }
  if (payload && typeof payload.detail === "string") {
    return new ApiError(payload.detail, status, "internal_error");
  }
  return new ApiError("La requête a échoué.", status, "internal_error");
}

async function request(path, options = {}) {
  const { method = "GET", body, auth = true, headers = {} } = options;
  const requestHeaders = { ...headers };
  if (auth && accessToken) {
    requestHeaders.Authorization = `Bearer ${accessToken}`;
  }
  let payload;
  if (body instanceof FormData) {
    payload = body;
  } else if (body !== undefined) {
    requestHeaders["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(`${BASE}${path}`, {
      method,
      headers: requestHeaders,
      body: payload,
    });
  } catch {
    throw new ApiError(
      "Le service est injoignable. Vérifiez la connexion puis réessayez.",
      0,
      "network"
    );
  }

  if (!response.ok) {
    let data = null;
    try {
      data = await response.json();
    } catch {
      data = null;
    }
    if (response.status === 401 && !path.startsWith("/auth/login")) {
      window.dispatchEvent(new Event("veda:unauthorized"));
    }
    throw errorFromPayload(data, response.status);
  }

  if (response.status === 204) {
    return null;
  }
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response;
}

export const api = {
  health: () => request("/health", { auth: false }),
  login: (email, password) =>
    request("/auth/login", {
      method: "POST",
      auth: false,
      body: { email, password },
    }),
  updateProfile: (displayName) =>
    request("/auth/me", {
      method: "PATCH",
      body: { display_name: displayName },
    }),
  changePassword: (currentPassword, newPassword) =>
    request("/auth/change-password", {
      method: "POST",
      body: {
        current_password: currentPassword,
        new_password: newPassword,
      },
    }),
  listFilings: (params = {}) => {
    const search = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        search.set(key, String(value));
      }
    });
    const query = search.toString();
    return request(`/filings${query ? `?${query}` : ""}`);
  },
  getFiling: (id) => request(`/filings/${id}`),
  getTimeline: (id) => request(`/filings/${id}/timeline`),
  getCredential: (id) => request(`/filings/${id}/credential`),
  verifyFiling: (id) =>
    request(`/filings/${id}/verify`, { method: "POST" }),
  downloadReport: (id) => request(`/filings/${id}/report.xlsx`),
  getReportPreview: (id) => request(`/filings/${id}/report.preview`),
  submitFiling: (file, fields) => {
    const body = new FormData();
    body.append("file", file);
    Object.entries(fields).forEach(([key, value]) => {
      body.append(key, String(value));
    });
    return request("/filings", { method: "POST", body });
  },
  extractFiling: (id, file) => {
    const body = new FormData();
    body.append("file", file);
    return request(`/filings/${id}/extract`, { method: "POST", body });
  },
  sealFiling: (id) =>
    request(`/filings/${id}/seal`, { method: "POST" }),
  rebuildCache: () => request("/system/rebuild", { method: "POST" }),
};
