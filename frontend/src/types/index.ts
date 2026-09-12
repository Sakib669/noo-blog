export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  bio?: string | null;
  avatar?: string | null;
  created_at: string;
}

export interface PublicUser {
  id: string;
  username: string;
  full_name: string;
  bio?: string | null;
  avatar?: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface PostAuthor {
  id: string;
  username: string;
  full_name: string;
  avatar?: string | null;
}

export interface Post {
  id: string;
  title: string;
  slug: string;
  content: string;
  summary?: string | null;
  cover_image?: string | null;
  published: boolean;
  views: number;
  tags: string[];
  created_at: string;
  updated_at: string;
  author?: PostAuthor | null;
}

export interface Comment {
  id: string;
  content: string;
  created_at: string;
  post_id: string;
  author?: PostAuthor | null;
}

export interface PostCreateInput {
  title: string;
  content: string;
  summary?: string;
  cover_image?: string;
  tags?: string[];
}

export interface PostUpdateInput {
  title?: string;
  content?: string;
  summary?: string;
  cover_image?: string;
  tags?: string[];
  published?: boolean;
}

export interface UserUpdateInput {
  full_name?: string;
  bio?: string;
  avatar?: string;
}

export interface PasswordChangeInput {
  current_password: string;
  new_password: string;
}
