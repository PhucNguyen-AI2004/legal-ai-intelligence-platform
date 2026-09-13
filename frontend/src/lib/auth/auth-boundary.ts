export interface AuthUser {
  id: string;
  email: string;
  fullName: string;
}

export interface AuthSession {
  user: AuthUser;
  accessToken: string;
}

export interface AuthBoundary {
  getSession(): Promise<AuthSession | null>;
  signIn(email: string, password: string): Promise<AuthSession>;
  signOut(): Promise<void>;
}

// Phase 8B will provide the implementation. UI components should depend on this
// boundary instead of reading or persisting JWTs directly.
