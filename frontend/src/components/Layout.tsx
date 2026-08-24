import { NavLink } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "../context/AuthContext";

export function Layout({ children }: { children: ReactNode }) {
  const { signOut, session } = useAuth();
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="brand">Document Summary Assistant</p>
          <p className="muted small">{session?.user.email}</p>
        </div>
        <nav>
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/history">History</NavLink>
          <button type="button" className="linkish" onClick={() => void signOut()}>
            Logout
          </button>
        </nav>
      </header>
      <main className="page">{children}</main>
    </div>
  );
}
