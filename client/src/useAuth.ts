import { useState, useEffect } from "react";
import { apiGet, apiPost, apiPut, apiPostFormData } from "./api";

export interface User {
  id: number;
  real_name: string;
  nickname: string;
  email: string;
  profile_image_url: string | null;
  created_at: string;
}

interface SignupData {
  real_name: string;
  nickname: string;
  email: string;
  password: string;
  password_confirm: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // 마운트 시 토큰이 있으면 유저 정보 가져오기
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      apiGet("/api/auth/me")
        .then((res) => {
          if (res.ok) return res.json();
          throw new Error("인증 실패");
        })
        .then((data) => setUser(data))
        .catch(() => {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const res = await apiPost("/api/auth/login", { email, password });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "로그인에 실패했습니다.");
    }
    const data = await res.json();
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    setUser(data.user);
  };

  const signup = async (signupData: SignupData) => {
    const res = await apiPost("/api/auth/signup", signupData);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "회원가입에 실패했습니다.");
    }
    const data = await res.json();
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    setUser(data.user);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  };

  const refreshUser = async () => {
    const res = await apiGet("/api/auth/me");
    if (res.ok) {
      const data = await res.json();
      setUser(data);
    }
  };

  const updateProfile = async (data: { real_name?: string; nickname?: string }) => {
    const res = await apiPut("/api/auth/me", data);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "프로필 수정에 실패했습니다.");
    }
    const updated = await res.json();
    setUser(updated);
  };

  const uploadProfileImage = async (file: File) => {
    const formData = new FormData();
    formData.append("image", file);
    const res = await apiPostFormData("/api/auth/profile-image", formData);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "이미지 업로드에 실패했습니다.");
    }
    const updated = await res.json();
    setUser(updated);
  };

  return {
    user,
    loading,
    login,
    signup,
    logout,
    refreshUser,
    updateProfile,
    uploadProfileImage,
  };
}
