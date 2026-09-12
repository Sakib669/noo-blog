import {
  Comment,
  PasswordChangeInput,
  Post,
  PostCreateInput,
  PostUpdateInput,
  PublicUser,
  TokenResponse,
  User,
  UserUpdateInput,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = "An error occurred";
    let data = null;
    try {
      data = await response.json();
      if (typeof data.detail === "string") {
        errorMessage = data.detail;
      } else if (Array.isArray(data.detail)) {
        errorMessage = data.detail.map((e: any) => e.msg || JSON.stringify(e)).join(", ");
      }
    } catch {
      errorMessage = response.statusText || errorMessage;
    }
    throw new ApiError(errorMessage, response.status, data);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}

export const api = {
  // Auth
  async register(body: { email: string; username: string; password: string; full_name: string }): Promise<TokenResponse> {
    return request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  async login(body: { email: string; password: string }): Promise<TokenResponse> {
    return request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  async getMe(): Promise<User> {
    return request<User>("/auth/me");
  },

  // Users
  async getUser(id: string): Promise<PublicUser> {
    return request<PublicUser>(`/users/${id}`);
  },

  async updateMe(body: UserUpdateInput): Promise<User> {
    return request<User>("/users/me", {
      method: "PUT",
      body: JSON.stringify(body),
    });
  },

  async changePassword(body: PasswordChangeInput): Promise<{ message: string }> {
    return request<{ message: string }>("/users/me/password", {
      method: "PUT",
      body: JSON.stringify(body),
    });
  },

  // Posts
  async getPosts(params?: { skip?: number; limit?: number; tag?: string; search?: string }): Promise<Post[]> {
    const query = new URLSearchParams();
    if (params?.skip !== undefined) query.set("skip", params.skip.toString());
    if (params?.limit !== undefined) query.set("limit", params.limit.toString());
    if (params?.tag) query.set("tag", params.tag);
    if (params?.search) query.set("search", params.search);

    const qs = query.toString();
    return request<Post[]>(`/posts/${qs ? `?${qs}` : ""}`);
  },

  async getPostBySlug(slug: string): Promise<Post> {
    return request<Post>(`/posts/${encodeURIComponent(slug)}`);
  },

  async createPost(body: PostCreateInput): Promise<Post> {
    return request<Post>("/posts/", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  async updatePost(postId: string, body: PostUpdateInput): Promise<Post> {
    return request<Post>(`/posts/${postId}`, {
      method: "PUT",
      body: JSON.stringify(body),
    });
  },

  async deletePost(postId: string): Promise<void> {
    return request<void>(`/posts/${postId}`, {
      method: "DELETE",
    });
  },

  async togglePublish(postId: string): Promise<Post> {
    return request<Post>(`/posts/${postId}/publish`, {
      method: "PATCH",
    });
  },

  async summarizePost(postId: string, force = false): Promise<Post> {
    return request<Post>(`/posts/${postId}/summarize${force ? "?force=true" : ""}`, {
      method: "POST",
    });
  },

  // Comments
  async getComments(postId: string): Promise<Comment[]> {
    return request<Comment[]>(`/posts/${postId}/comments`);
  },

  async createComment(postId: string, content: string): Promise<Comment> {
    return request<Comment>(`/posts/${postId}/comments`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });
  },

  async deleteComment(commentId: string): Promise<void> {
    return request<void>(`/comments/${commentId}`, {
      method: "DELETE",
    });
  },
};
