import { useState } from "react";
import { NavLink } from "react-router-dom";

import { useAuth } from "../auth/useAuth";
import { ROLE_LABELS } from "../labels/fr";
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
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-2 px-4 py-2">
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
          {/* Who you are signed in as. The session is one cookie per browser, so
              logging in as somebody else silently replaces it; without this the
              only way to tell them apart is to notice which menus disappeared. */}
          <span
            className="ml-3 flex items-center gap-2 border-l border-white/25 pl-3"
            title={`${currentUser.email} (${ROLE_LABELS[currentUser.role]})`}
          >
            {/* The role stays visible at every width because it is the part that
                answers "why can I not see this"; the address folds away first. */}
            <span className="hidden max-w-[16rem] truncate text-xs text-white/85 lg:inline">
              {currentUser.email}
            </span>
            <span className="whitespace-nowrap rounded-full bg-white/15 px-2 py-0.5 text-[11px] font-medium">
              {ROLE_LABELS[currentUser.role]}
            </span>
          </span>
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
          <div className="border-b border-white/20 py-2">
            <p className="truncate text-sm">{currentUser.email}</p>
            <p className="text-xs text-white/70">
              {ROLE_LABELS[currentUser.role]}
            </p>
          </div>
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
