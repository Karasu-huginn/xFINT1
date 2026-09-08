import { useState } from "react";
import { NavLink } from "react-router-dom";

import { useAuth } from "../auth/useAuth";
import type { Role } from "../types/api";

interface NavEntry {
  to: string;
  label: string;
  allowedRoles: Role[];
}

const EVERY_ROLE: Role[] = ["EMPLOYEE", "MANAGER", "ACCOUNTING"];

const NAV_ENTRIES: NavEntry[] = [
  { to: "/expenses", label: "Mes notes", allowedRoles: EVERY_ROLE },
  { to: "/expenses/new", label: "Nouvelle note", allowedRoles: EVERY_ROLE },
  {
    to: "/expenses/all",
    label: "Toutes les notes",
    allowedRoles: ["MANAGER", "ACCOUNTING"],
  },
  { to: "/users/new", label: "Créer un compte", allowedRoles: ["MANAGER"] },
  { to: "/profile", label: "Profil", allowedRoles: EVERY_ROLE },
];

function buildLinkClasses({ isActive }: { isActive: boolean }): string {
  const base = "block rounded px-3 py-2 text-sm transition-colors md:inline-block";
  if (isActive) {
    return `${base} bg-primary-dark text-white`;
  }
  return `${base} text-white/85 hover:bg-primary-dark hover:text-white`;
}

export default function Navbar() {
  const { currentUser, signOut } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  if (currentUser === null) {
    return null;
  }

  const visibleEntries = NAV_ENTRIES.filter((entry) =>
    entry.allowedRoles.includes(currentUser.role),
  );

  return (
    <header className="bg-primary text-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-2">
        <span className="text-base font-semibold tracking-wide">SUP Herman</span>
        <button
          type="button"
          aria-label="Ouvrir le menu"
          aria-expanded={isMenuOpen}
          className="rounded px-2 py-1 text-xl leading-none hover:bg-primary-dark md:hidden"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
        >
          &#9776;
        </button>
        <nav className="hidden items-center gap-1 md:flex">
          {visibleEntries.map((entry) => (
            <NavLink key={entry.to} to={entry.to} className={buildLinkClasses} end>
              {entry.label}
            </NavLink>
          ))}
          <button
            type="button"
            onClick={() => void signOut()}
            className="ml-2 rounded border border-white/40 px-3 py-1.5 text-sm hover:bg-primary-dark"
          >
            Déconnexion
          </button>
        </nav>
      </div>
      {isMenuOpen && (
        <nav className="border-t border-white/20 px-4 pb-3 md:hidden">
          {visibleEntries.map((entry) => (
            <NavLink
              key={entry.to}
              to={entry.to}
              className={buildLinkClasses}
              onClick={() => setIsMenuOpen(false)}
              end
            >
              {entry.label}
            </NavLink>
          ))}
          <button
            type="button"
            onClick={() => void signOut()}
            className="mt-2 w-full rounded border border-white/40 px-3 py-2 text-sm hover:bg-primary-dark"
          >
            Déconnexion
          </button>
        </nav>
      )}
    </header>
  );
}
